"""Data archival manager for retention policies."""

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..utils.logging import get_logger
from .retention_policies import ArchivalStrategy, DataType, RetentionPolicy


@dataclass
class ArchivalLocation:
    """Configuration for an archival location."""

    name: str
    type: str  # local, s3, gcs, azure
    path: str
    credentials: dict[str, Any] | None = None
    compression: bool = True
    encryption: bool = False
    retention_days: int | None = None
    max_size_gb: float | None = None


@dataclass
class ArchivalJob:
    """An archival job for a specific policy."""

    id: str
    policy: RetentionPolicy
    location: ArchivalLocation
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    records_archived: int = 0
    storage_archived_mb: float = 0.0
    archive_path: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class ArchivalMetadata:
    """Metadata for archived data."""

    policy_name: str
    data_type: DataType
    archival_strategy: ArchivalStrategy
    original_count: int
    archived_count: int
    compression_ratio: float
    archival_timestamp: str
    retention_policy: dict[str, Any]
    data_schema: dict[str, Any]
    checksum: str


class ArchivalManager:
    """Manager for data archival operations."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize the archival manager."""
        self.config = config or {}
        self.logger = get_logger(__name__)

        # Configuration
        self.default_archival_path = self.config.get(
            "default_archival_path", "./archives"
        )
        self.max_concurrent_jobs = self.config.get("max_concurrent_jobs", 2)
        self.job_timeout = self.config.get("job_timeout", 600)  # 10 minutes
        self.batch_size = self.config.get("batch_size", 5000)
        self.compression_level = self.config.get("compression_level", 6)

        # Job management
        self.jobs: dict[str, ArchivalJob] = {}
        self.running_jobs: dict[str, ArchivalJob] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()

        # State
        self.is_running = False
        self.worker_tasks: list[asyncio.Task] = []

        # Archival locations
        self.locations: dict[str, ArchivalLocation] = {}
        self._initialize_default_locations()

        # Statistics
        self.total_jobs_processed = 0
        self.total_records_archived = 0
        self.total_storage_archived_mb = 0.0

    def _initialize_default_locations(self) -> None:
        """Initialize default archival locations."""
        default_local = ArchivalLocation(
            name="default_local",
            type="local",
            path=self.default_archival_path,
            compression=True,
            encryption=False,
            retention_days=365 * 5,  # 5 years
        )

        self.locations["default_local"] = default_local

        # Create directory if it doesn't exist
        os.makedirs(self.default_archival_path, exist_ok=True)

    async def start(self) -> None:
        """Start the archival manager."""
        if self.is_running:
            self.logger.warning("Archival manager is already running")
            return

        try:
            self.is_running = True

            # Start worker tasks
            for i in range(self.max_concurrent_jobs):
                task = asyncio.create_task(self._worker(f"archival-worker-{i}"))
                self.worker_tasks.append(task)

            self.logger.info(
                f"Archival manager started with {self.max_concurrent_jobs} workers"
            )

        except Exception as e:
            self.logger.error(f"Error starting archival manager: {e}")
            self.is_running = False
            raise

    async def stop(self) -> None:
        """Stop the archival manager."""
        if not self.is_running:
            return

        try:
            self.is_running = False

            # Cancel all worker tasks
            for task in self.worker_tasks:
                task.cancel()

            # Wait for tasks to complete
            if self.worker_tasks:
                await asyncio.gather(*self.worker_tasks, return_exceptions=True)
                self.worker_tasks.clear()

            # Cancel running jobs
            for job in self.running_jobs.values():
                job.status = "cancelled"

            self.logger.info("Archival manager stopped")

        except Exception as e:
            self.logger.error(f"Error stopping archival manager: {e}")

    def add_location(self, location: ArchivalLocation) -> bool:
        """Add a new archival location."""
        try:
            if location.name in self.locations:
                self.logger.warning(f"Location '{location.name}' already exists")
                return False

            # Validate location
            if location.type == "local":
                os.makedirs(location.path, exist_ok=True)

            self.locations[location.name] = location
            self.logger.info(f"Added archival location: {location.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding location '{location.name}': {e}")
            return False

    def remove_location(self, name: str) -> bool:
        """Remove an archival location."""
        try:
            if name not in self.locations:
                return False

            # Check if it's the default location
            if name == "default_local":
                self.logger.warning("Cannot remove default local location")
                return False

            del self.locations[name]
            self.logger.info(f"Removed archival location: {name}")
            return True

        except Exception as e:
            self.logger.error(f"Error removing location '{name}': {e}")
            return False

    def get_location(self, name: str) -> ArchivalLocation | None:
        """Get an archival location by name."""
        return self.locations.get(name)

    def list_locations(self) -> list[str]:
        """List all archival location names."""
        return list(self.locations.keys())

    async def submit_archival_job(
        self, policy: RetentionPolicy, location_name: str
    ) -> str:
        """Submit an archival job for a policy."""
        try:
            if location_name not in self.locations:
                raise ValueError(f"Unknown archival location: {location_name}")

            location = self.locations[location_name]

            job_id = (
                f"archival_{policy.name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            )

            job = ArchivalJob(
                id=job_id,
                policy=policy,
                location=location,
                status="pending",
                created_at=datetime.utcnow(),
            )

            self.jobs[job_id] = job
            await self.job_queue.put(job)

            self.logger.info(
                f"Submitted archival job {job_id} for policy {policy.name}"
            )
            return job_id

        except Exception as e:
            self.logger.error(
                f"Error submitting archival job for policy {policy.name}: {e}"
            )
            raise

    async def get_job_status(self, job_id: str) -> ArchivalJob | None:
        """Get the status of an archival job."""
        return self.jobs.get(job_id)

    async def get_all_jobs(self) -> list[ArchivalJob]:
        """Get all archival jobs."""
        return list(self.jobs.values())

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running archival job."""
        try:
            if job_id not in self.jobs:
                return False

            job = self.jobs[job_id]
            if job.status == "running":
                job.status = "cancelled"
                if job_id in self.running_jobs:
                    del self.running_jobs[job_id]
                self.logger.info(f"Cancelled archival job {job_id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error cancelling job {job_id}: {e}")
            return False

    async def _worker(self, worker_name: str) -> None:
        """Worker task for processing archival jobs."""
        self.logger.debug(f"Worker {worker_name} started")

        while self.is_running:
            try:
                # Get job from queue
                try:
                    job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                except TimeoutError:
                    continue

                if not self.is_running:
                    break

                # Process the job
                await self._process_job(job, worker_name)

                # Mark job as done
                self.job_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)

        self.logger.debug(f"Worker {worker_name} stopped")

    async def _process_job(self, job: ArchivalJob, worker_name: str) -> None:
        """Process an archival job."""
        try:
            # Check if job was cancelled
            if job.status == "cancelled":
                return

            # Update job status
            job.status = "running"
            job.started_at = datetime.utcnow()
            self.running_jobs[job.id] = job

            self.logger.info(f"Worker {worker_name} processing archival job {job.id}")

            # Execute archival
            result = await self._execute_archival(job)

            # Update job with result
            job.records_archived = result.get("records_archived", 0)
            job.storage_archived_mb = result.get("storage_archived_mb", 0.0)
            job.archive_path = result.get("archive_path")
            job.metadata = result.get("metadata")
            job.status = "completed"
            job.completed_at = datetime.utcnow()

            # Update statistics
            self.total_jobs_processed += 1
            self.total_records_archived += job.records_archived
            self.total_storage_archived_mb += job.storage_archived_mb

            # Remove from running jobs
            if job.id in self.running_jobs:
                del self.running_jobs[job.id]

            self.logger.info(f"Archival job {job.id} completed successfully")

        except Exception as e:
            self.logger.error(f"Error processing archival job {job.id}: {e}")

            # Update job status
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            job.error_message = str(e)

            # Remove from running jobs
            if job.id in self.running_jobs:
                del self.running_jobs[job.id]

    async def _execute_archival(self, job: ArchivalJob) -> dict[str, Any]:
        """Execute archival for a specific job."""
        try:
            self.logger.info(f"Starting archival for policy: {job.policy.name}")

            # Determine archival strategy
            if job.policy.archival_strategy == ArchivalStrategy.ARCHIVE:
                result = await self._archive_data(job)
            elif job.policy.archival_strategy == ArchivalStrategy.COMPRESS:
                result = await self._compress_data(job)
            elif job.policy.archival_strategy == ArchivalStrategy.SAMPLE:
                result = await self._sample_data(job)
            elif job.policy.archival_strategy == ArchivalStrategy.AGGREGATE:
                result = await self._aggregate_data(job)
            else:
                raise ValueError(
                    f"Unsupported archival strategy: {job.policy.archival_strategy}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Archival failed for policy {job.policy.name}: {e}")
            raise

    async def _archive_data(self, job: ArchivalJob) -> dict[str, Any]:
        """Archive data according to policy."""
        try:
            # This is a placeholder - actual archival logic will be implemented
            # based on the data type and storage backend
            self.logger.debug(f"Archive data placeholder for policy: {job.policy.name}")

            # Simulate archival process
            records_archived = 1000  # Placeholder
            storage_archived_mb = 50.0  # Placeholder

            # Generate archive path
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            archive_filename = f"{job.policy.name}_{timestamp}.json.gz"
            archive_path = os.path.join(job.location.path, archive_filename)

            # Create metadata
            metadata = ArchivalMetadata(
                policy_name=job.policy.name,
                data_type=job.policy.data_type,
                archival_strategy=job.policy.archival_strategy,
                original_count=records_archived,
                archived_count=records_archived,
                compression_ratio=0.7,
                archival_timestamp=datetime.utcnow().isoformat(),
                retention_policy=job.policy.__dict__,
                data_schema={"fields": [], "tags": []},
                checksum="placeholder_checksum",
            )

            # Write metadata file
            metadata_path = archive_path.replace(".json.gz", ".metadata.json")
            with open(metadata_path, "w") as f:
                json.dump(metadata.__dict__, f, indent=2, default=str)

            return {
                "records_archived": records_archived,
                "storage_archived_mb": storage_archived_mb,
                "archive_path": archive_path,
                "metadata": metadata.__dict__,
            }

        except Exception as e:
            self.logger.error(f"Error in _archive_data: {e}")
            raise

    async def _compress_data(self, job: ArchivalJob) -> dict[str, Any]:
        """Compress data according to policy."""
        # This is a placeholder - actual compression logic will be implemented
        self.logger.debug(f"Compress data placeholder for policy: {job.policy.name}")

        return {
            "records_archived": 0,
            "storage_archived_mb": 0.0,
            "archive_path": None,
            "metadata": None,
        }

    async def _sample_data(self, job: ArchivalJob) -> dict[str, Any]:
        """Sample data according to policy."""
        # This is a placeholder - actual sampling logic will be implemented
        self.logger.debug(f"Sample data placeholder for policy: {job.policy.name}")

        return {
            "records_archived": 0,
            "storage_archived_mb": 0.0,
            "archive_path": None,
            "metadata": None,
        }

    async def _aggregate_data(self, job: ArchivalJob) -> dict[str, Any]:
        """Aggregate data according to policy."""
        # This is a placeholder - actual aggregation logic will be implemented
        self.logger.debug(f"Aggregate data placeholder for policy: {job.policy.name}")

        return {
            "records_archived": 0,
            "storage_archived_mb": 0.0,
            "archive_path": None,
            "metadata": None,
        }

    async def list_archives(self, location_name: str) -> list[dict[str, Any]]:
        """List all archives in a location."""
        try:
            if location_name not in self.locations:
                return []

            location = self.locations[location_name]

            if location.type != "local":
                self.logger.warning(
                    f"Listing archives not supported for location type: {location.type}"
                )
                return []

            archives = []
            archive_dir = Path(location.path)

            if not archive_dir.exists():
                return []

            for file_path in archive_dir.glob("*.json.gz"):
                try:
                    # Get file info
                    stat = file_path.stat()

                    # Try to find corresponding metadata
                    metadata_path = file_path.with_suffix(".metadata.json")
                    metadata = {}

                    if metadata_path.exists():
                        with open(metadata_path) as f:
                            metadata = json.load(f)

                    archives.append(
                        {
                            "filename": file_path.name,
                            "size_mb": stat.st_size / (1024 * 1024),
                            "created_at": datetime.fromtimestamp(
                                stat.st_ctime
                            ).isoformat(),
                            "modified_at": datetime.fromtimestamp(
                                stat.st_mtime
                            ).isoformat(),
                            "metadata": metadata,
                        }
                    )

                except Exception as e:
                    self.logger.warning(f"Error reading archive {file_path}: {e}")
                    continue

            # Sort by creation time (newest first)
            archives.sort(key=lambda x: x["created_at"], reverse=True)

            return archives

        except Exception as e:
            self.logger.error(
                f"Error listing archives for location {location_name}: {e}"
            )
            return []

    async def cleanup_old_archives(self, location_name: str) -> dict[str, Any]:
        """Clean up old archives based on retention policies."""
        try:
            if location_name not in self.locations:
                return {"success": False, "error": "Unknown location"}

            location = self.locations[location_name]

            if not location.retention_days:
                return {"success": False, "error": "No retention policy for location"}

            archives = await self.list_archives(location_name)
            cutoff_date = datetime.utcnow() - timedelta(days=location.retention_days)

            deleted_count = 0
            freed_space_mb = 0.0

            for archive in archives:
                try:
                    archive_date = datetime.fromisoformat(archive["created_at"])

                    if archive_date < cutoff_date:
                        # Delete archive file
                        archive_path = Path(location.path) / archive["filename"]
                        metadata_path = archive_path.with_suffix(".metadata.json")

                        if archive_path.exists():
                            archive_path.unlink()
                            deleted_count += 1
                            freed_space_mb += archive["size_mb"]

                        if metadata_path.exists():
                            metadata_path.unlink()

                        self.logger.info(f"Deleted old archive: {archive['filename']}")

                except Exception as e:
                    self.logger.warning(
                        f"Error processing archive {archive['filename']}: {e}"
                    )
                    continue

            return {
                "success": True,
                "deleted_count": deleted_count,
                "freed_space_mb": freed_space_mb,
            }

        except Exception as e:
            self.logger.error(
                f"Error cleaning up old archives for location {location_name}: {e}"
            )
            return {"success": False, "error": str(e)}

    def get_statistics(self) -> dict[str, Any]:
        """Get archival manager statistics."""
        return {
            "total_jobs_processed": self.total_jobs_processed,
            "total_records_archived": self.total_records_archived,
            "total_storage_archived_mb": self.total_storage_archived_mb,
            "active_jobs": len(self.running_jobs),
            "queued_jobs": self.job_queue.qsize(),
            "total_jobs": len(self.jobs),
            "locations": len(self.locations),
            "is_running": self.is_running,
            "worker_count": len(self.worker_tasks),
        }
