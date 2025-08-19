"""Domain-based filter for Home Assistant events."""

from ..models.events import Event
from .base import Filter


class DomainFilter(Filter):
    """Filter events based on their domain."""

    def __init__(self, domains: list[str] | str, name: str | None = None):
        """Initialize domain filter.

        Args:
            domains: List of domains to allow, or single domain string
            name: Optional name for the filter
        """
        super().__init__(
            name or f"domain_filter_{'_'.join(self._normalize_domains(domains))}"
        )

        # Normalize domains to list
        self.domains = self._normalize_domains(domains)

        # Create set for O(1) lookup
        self._domain_set = set(self.domains)

        self.logger.info(
            "Domain filter initialized",
            allowed_domains=self.domains,
            total_domains=len(self.domains),
        )

    def _normalize_domains(self, domains: list[str] | str) -> list[str]:
        """Normalize domains input to a list.

        Args:
            domains: Input domains (string or list)

        Returns:
            Normalized list of domains
        """
        if isinstance(domains, str):
            return [domains]
        elif isinstance(domains, list):
            return [str(domain).lower().strip() for domain in domains if domain]
        else:
            raise ValueError("domains must be a string or list of strings")

    async def should_process(self, event: Event) -> bool:
        """Check if event domain is in the allowed list.

        Args:
            event: The event to check

        Returns:
            True if event domain is allowed, False otherwise
        """
        if not event.domain:
            self.logger.debug(
                "Event has no domain, filtering out", event_entity_id=event.entity_id
            )
            return False

        # Convert to lowercase for case-insensitive comparison
        event_domain = event.domain.lower().strip()

        # Check if domain is in allowed list
        should_process = event_domain in self._domain_set

        if should_process:
            self.logger.debug(
                "Event domain allowed", domain=event.domain, entity_id=event.entity_id
            )
        else:
            self.logger.debug(
                "Event domain filtered out",
                domain=event.domain,
                entity_id=event.entity_id,
                allowed_domains=self.domains,
            )

        return should_process

    def add_domain(self, domain: str) -> None:
        """Add a domain to the allowed list.

        Args:
            domain: Domain to add
        """
        normalized_domain = domain.lower().strip()
        if normalized_domain and normalized_domain not in self._domain_set:
            self.domains.append(normalized_domain)
            self._domain_set.add(normalized_domain)
            self.logger.info(
                "Added domain to filter",
                domain=normalized_domain,
                total_domains=len(self.domains),
            )

    def remove_domain(self, domain: str) -> bool:
        """Remove a domain from the allowed list.

        Args:
            domain: Domain to remove

        Returns:
            True if domain was removed, False if not found
        """
        normalized_domain = domain.lower().strip()
        if normalized_domain in self._domain_set:
            self.domains.remove(normalized_domain)
            self._domain_set.remove(normalized_domain)
            self.logger.info(
                "Removed domain from filter",
                domain=normalized_domain,
                total_domains=len(self.domains),
            )
            return True
        return False

    def get_allowed_domains(self) -> list[str]:
        """Get list of allowed domains.

        Returns:
            List of allowed domains
        """
        return self.domains.copy()

    def is_domain_allowed(self, domain: str) -> bool:
        """Check if a specific domain is allowed.

        Args:
            domain: Domain to check

        Returns:
            True if domain is allowed, False otherwise
        """
        return domain.lower().strip() in self._domain_set
