# 🔥 Pre-Rebuild Checklist - CRITICAL STEPS

**Date:** October 14, 2025  
**Purpose:** Ensure safe and complete system rebuild  
**⚠️ DO NOT SKIP ANY STEPS ⚠️**

---

## 🎯 Quick Overview

This checklist ensures you:
1. ✅ Back up all critical data
2. ✅ Validate current system state
3. ✅ **STOP AND DELETE all current containers** ← **CRITICAL**
4. ✅ Clean up images and networks
5. ✅ Prepare for fresh rebuild

**Estimated Time:** 20-30 minutes

---

## Phase 1: PRE-FLIGHT CHECKS (5 minutes)

### 1.1 Verify Current System Status

```bash
# Check running services
docker-compose ps

# Note how many services are running
# Expected: 13+ services
```

**Checklist:**
- [ ] All services currently running
- [ ] Can access dashboard at http://localhost:3000
- [ ] HA connection is working (check websocket logs)
- [ ] Data is accessible

### 1.2 Verify Docker is Working

```bash
# Check Docker version
docker --version
docker-compose --version

# Check disk space (need ~10GB free)
df -h  # Linux/Mac
Get-PSDrive  # Windows
```

**Checklist:**
- [ ] Docker is installed and running
- [ ] Docker Compose is available
- [ ] Sufficient disk space available (10GB+)
- [ ] No Docker errors or warnings

---

## Phase 2: BACKUP CRITICAL DATA (10-15 minutes)

### ⚠️ CRITICAL: Create Backups First!

**DO NOT PROCEED WITHOUT BACKUPS!**

### 2.1 Backup InfluxDB Data

```bash
# Create backup inside container
docker exec homeiq-influxdb influx backup /tmp/backup

# Copy backup to host
docker cp homeiq-influxdb:/tmp/backup ~/backup-$(date +%Y%m%d)-influxdb

# Verify backup
ls -lh ~/backup-$(date +%Y%m%d)-influxdb
```

**Windows PowerShell:**
```powershell
# Create backup inside container
docker exec homeiq-influxdb influx backup /tmp/backup

# Copy backup to host
$date = Get-Date -Format "yyyyMMdd"
docker cp homeiq-influxdb:/tmp/backup $HOME/backup-$date-influxdb

# Verify backup
Get-ChildItem $HOME/backup-$date-influxdb
```

**Checklist:**
- [ ] Backup created successfully
- [ ] Backup copied to host machine
- [ ] Backup files verified (multiple .tar.gz files)
- [ ] Backup size looks reasonable (>1MB typically)

### 2.2 Backup SQLite Database

```bash
# Backup metadata database
docker cp homeiq-data-api:/app/data/metadata.db ~/backup-$(date +%Y%m%d)-metadata.db

# Verify backup
ls -lh ~/backup-*-metadata.db
```

**Windows PowerShell:**
```powershell
# Backup metadata database
$date = Get-Date -Format "yyyyMMdd"
docker cp homeiq-data-api:/app/data/metadata.db $HOME/backup-$date-metadata.db

# Verify backup
Get-ChildItem $HOME/backup-*-metadata.db
```

**Checklist:**
- [ ] SQLite database backed up
- [ ] Backup file exists on host
- [ ] File size > 0 bytes

### 2.3 Backup Environment Files

```bash
# Backup main environment file
cp .env ~/backup-$(date +%Y%m%d)-env

# Backup infrastructure configs
cp infrastructure/.env.* ~/backup-$(date +%Y%m%d)-envconfigs/

# Verify backups
ls -lh ~/backup-*-env*
```

**Windows PowerShell:**
```powershell
# Backup main environment file
$date = Get-Date -Format "yyyyMMdd"
Copy-Item .env $HOME/backup-$date-env

# Backup infrastructure configs (if they exist)
if (Test-Path "infrastructure/.env.*") {
    New-Item -ItemType Directory -Force -Path "$HOME/backup-$date-envconfigs"
    Copy-Item infrastructure/.env.* "$HOME/backup-$date-envconfigs/"
}

# Verify backups
Get-ChildItem $HOME/backup-*-env*
```

**Checklist:**
- [ ] .env file backed up
- [ ] Infrastructure configs backed up
- [ ] Backup files verified

### 2.4 Backup Docker Compose Configuration

```bash
# Backup current compose file
cp docker-compose.yml ~/backup-$(date +%Y%m%d)-docker-compose.yml

# Verify backup
ls -lh ~/backup-*-docker-compose.yml
```

**Windows PowerShell:**
```powershell
# Backup current compose file
$date = Get-Date -Format "yyyyMMdd"
Copy-Item docker-compose.yml $HOME/backup-$date-docker-compose.yml

# Verify backup
Get-ChildItem $HOME/backup-*-docker-compose.yml
```

**Checklist:**
- [ ] docker-compose.yml backed up
- [ ] Backup file verified

---

## Phase 3: 🔥 STOP AND DELETE CURRENT DEPLOYMENT 🔥

### ⚠️ CRITICAL STEP - Point of No Return

**This is where we destroy the current deployment!**

### Option A: Use Automated Script (RECOMMENDED)

**Linux/Mac:**
```bash
# Run the automated teardown script
./scripts/stop-and-remove-all.sh

# The script will:
# 1. Ask for backup confirmation
# 2. Stop all services
# 3. Remove all containers
# 4. Remove all images
# 5. Remove networks
# 6. Clean build cache
# 7. Verify cleanup
```

**Windows:**
```powershell
# Run the automated teardown script
.\scripts\stop-and-remove-all.ps1

# The script will:
# 1. Ask for backup confirmation
# 2. Stop all services
# 3. Remove all containers
# 4. Remove all images
# 5. Remove networks
# 6. Clean build cache
# 7. Verify cleanup
```

**Checklist:**
- [ ] Script completed without errors
- [ ] All containers removed (verification shown)
- [ ] All images removed (verification shown)
- [ ] Networks removed (verification shown)

### Option B: Manual Teardown (If Script Fails)

```bash
# Step 1: Stop services gracefully
docker-compose down --timeout 30

# Step 2: Force stop any remaining containers
docker ps --filter "name=homeiq" -q | xargs -r docker stop

# Step 3: Remove all containers
docker ps -a --filter "name=homeiq" -q | xargs -r docker rm -f

# Step 4: Remove all images
docker images --filter=reference='*homeiq*' -q | xargs -r docker rmi -f

# Step 5: Remove networks
docker network rm homeiq-network 2>/dev/null || true
docker network rm homeiq-network-dev 2>/dev/null || true

# Step 6: Clean build cache
docker builder prune -a -f
```

**Windows PowerShell:**
```powershell
# Step 1: Stop services gracefully
docker-compose down --timeout 30

# Step 2: Force stop any remaining containers
docker ps --filter "name=homeiq" -q | ForEach-Object { docker stop $_ }

# Step 3: Remove all containers
docker ps -a --filter "name=homeiq" -q | ForEach-Object { docker rm -f $_ }

# Step 4: Remove all images
docker images --filter=reference='*homeiq*' -q | ForEach-Object { docker rmi -f $_ }

# Step 5: Remove networks
docker network rm homeiq-network 2>$null
docker network rm homeiq-network-dev 2>$null

# Step 6: Clean build cache
docker builder prune -a -f
```

**Checklist:**
- [ ] Services stopped
- [ ] All containers removed
- [ ] All images removed
- [ ] Networks removed
- [ ] Build cache cleaned

---

## Phase 4: VERIFY COMPLETE CLEANUP (5 minutes)

### 4.1 Verify No Containers Remain

```bash
# Check for remaining containers
docker ps -a | grep homeiq

# Should show NO results
```

**Expected:** Command should return nothing or "no rows"

**Checklist:**
- [ ] No homeiq containers found
- [ ] `docker ps -a` shows clean state

### 4.2 Verify No Images Remain

```bash
# Check for remaining images
docker images | grep homeiq

# Should show NO results
```

**Expected:** Command should return nothing or "no rows"

**Checklist:**
- [ ] No homeiq images found
- [ ] `docker images` shows clean state

### 4.3 Verify No Networks Remain

```bash
# Check for remaining networks
docker network ls | grep homeiq

# Should show NO results
```

**Expected:** Command should return nothing or "no rows"

**Checklist:**
- [ ] No homeiq networks found
- [ ] Only default Docker networks remain

### 4.4 Verify Volumes Preserved (IMPORTANT)

```bash
# Check volumes are still there
docker volume ls | grep homeiq

# Should show volumes like:
# - homeiq_influxdb_data
# - homeiq_influxdb_config
# - homeiq_sqlite-data
# - homeiq_data_retention_backups
```

**Expected:** Volumes should still exist (containing your data)

**Checklist:**
- [ ] influxdb_data volume exists
- [ ] influxdb_config volume exists
- [ ] sqlite-data volume exists
- [ ] data_retention_backups volume exists

---

## Phase 5: FINAL PRE-REBUILD CHECKS (5 minutes)

### 5.1 Verify Git Status

```bash
# Check what files changed
git status

# Review changes made
git diff docker-compose.yml
```

**Checklist:**
- [ ] docker-compose.yml shows data-api dependency added
- [ ] .dockerignore file exists
- [ ] No unexpected changes

### 5.2 Validate Docker Compose Configuration

```bash
# Validate syntax (should show no errors)
docker-compose config > /dev/null
echo "Exit code: $?"  # Should be 0

# View the processed config (optional)
docker-compose config | less
```

**Checklist:**
- [ ] Configuration is valid (exit code 0)
- [ ] No syntax errors
- [ ] All services defined correctly

### 5.3 Verify Environment Files

```bash
# Check .env exists
ls -la .env

# Check infrastructure configs
ls -la infrastructure/.env.*
```

**Checklist:**
- [ ] .env file exists
- [ ] Contains required variables
- [ ] No placeholder values (your_token_here)

### 5.4 Check Disk Space

```bash
# Check available space
df -h  # Linux/Mac
Get-PSDrive  # Windows

# Need at least 10GB free
```

**Checklist:**
- [ ] At least 10GB free space
- [ ] No disk space warnings

---

## 📋 MASTER CHECKLIST

### Pre-Flight ✅
- [ ] Current system status verified
- [ ] Docker is working
- [ ] Sufficient disk space

### Backups ✅
- [ ] InfluxDB data backed up
- [ ] SQLite database backed up
- [ ] Environment files backed up
- [ ] docker-compose.yml backed up
- [ ] All backups verified

### Teardown ✅
- [ ] Automated script ran successfully OR
- [ ] Manual teardown completed
- [ ] Services stopped
- [ ] Containers removed
- [ ] Images removed
- [ ] Networks removed
- [ ] Build cache cleaned

### Verification ✅
- [ ] No containers remain
- [ ] No images remain
- [ ] No networks remain
- [ ] Volumes preserved (data intact)

### Final Checks ✅
- [ ] Git status reviewed
- [ ] Docker Compose config valid
- [ ] Environment files present
- [ ] Disk space sufficient

---

## ✅ READY TO REBUILD?

If all checkboxes above are checked, you are **READY TO PROCEED** with the rebuild!

### Next Steps:

1. **Rebuild Images** (20 minutes)
   ```bash
   docker-compose build --no-cache --parallel
   ```

2. **Deploy Services** (5 minutes)
   ```bash
   docker-compose up -d
   ```

3. **Monitor Startup** (5 minutes)
   ```bash
   watch -n 2 'docker-compose ps'
   # Wait for all services to show "Up (healthy)"
   ```

4. **Validate System** (10 minutes)
   ```bash
   ./scripts/test-services.sh
   curl http://localhost:3000
   ```

**Full procedure:** `implementation/COMPLETE_SYSTEM_REBUILD_PLAN.md`

---

## 🆘 Emergency Rollback

If you need to abort and restore:

```bash
# 1. Stop any partial rebuild
docker-compose down

# 2. Restore InfluxDB
docker-compose up -d influxdb
docker cp ~/backup-YYYYMMDD-influxdb homeiq-influxdb:/tmp/backup
docker exec homeiq-influxdb influx restore /tmp/backup

# 3. Restore SQLite
docker-compose up -d data-api
docker cp ~/backup-YYYYMMDD-metadata.db homeiq-data-api:/app/data/metadata.db

# 4. Restore environment
cp ~/backup-YYYYMMDD-env .env

# 5. Start all services
docker-compose up -d
```

---

## 📊 Checklist Status

**Total Items:** 40+  
**Completed:** _____ / 40+

**Progress:**
- [ ] Phase 1: Pre-Flight Checks
- [ ] Phase 2: Backup Critical Data
- [ ] Phase 3: Stop and Delete Deployment
- [ ] Phase 4: Verify Complete Cleanup
- [ ] Phase 5: Final Pre-Rebuild Checks

**Status:** 🟡 In Progress → 🟢 Ready to Rebuild

---

**Once all phases complete, proceed to rebuild using:**
- `implementation/COMPLETE_SYSTEM_REBUILD_PLAN.md` (Phase 3+)
- `implementation/REBUILD_QUICK_REFERENCE.md` (Quick commands)

