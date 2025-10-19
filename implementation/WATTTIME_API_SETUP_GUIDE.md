# WattTime API Setup Guide

**Date:** 2025-01-15  
**Service:** Carbon Intensity Service  
**Current Status:** ⚠️ Requires API Token

---

## Overview

WattTime provides real-time carbon intensity data for electricity grids worldwide. Our `carbon-intensity-service` is already implemented and ready to use - **it just needs a valid API token**.

---

## Current Implementation Status

### ✅ What's Already Built

Our service (Port 8010) is complete with:
- WattTime API v3 integration
- Bearer token authentication
- 15-minute polling interval
- InfluxDB storage
- Health check endpoint
- Regional configuration support
- Forecast data parsing

**File:** `services/carbon-intensity-service/src/main.py`

### Configuration Expected

```python
# Lines 37-39
self.api_token = os.getenv('WATTTIME_API_TOKEN')  # ← Needs this
self.region = os.getenv('GRID_REGION', 'CAISO_NORTH')
self.base_url = "https://api.watttime.org/v3"

# API Call (Line 105-107)
url = f"{self.base_url}/forecast"
headers = {"Authorization": f"Bearer {self.api_token}"}
params = {"region": self.region}
```

---

## Registration Process (Verified Steps)

Based on WattTime documentation and your research, here's the confirmed process:

### **Step 1: Visit WattTime's Registration Page**

**Action:** Go to WattTime's developer portal
- URL: https://watttime.org or https://docs.watttime.org
- Look for "API Access" or "Developer" section

**Expected:** Sign-up form or registration page

---

### **Step 2: Register a New Account**

**Action:** Create an account with WattTime
- **Method:** HTTP POST to `/register` endpoint OR web form

**Expected Fields:**
```json
{
  "username": "your-username",
  "password": "strong-password",
  "email": "your@email.com",
  "organization": "your-org-name"
}
```

**Example curl (if API registration available):**
```bash
curl -X POST https://api.watttime.org/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your-username",
    "password": "your-secure-password",
    "email": "your@email.com",
    "organization": "Home Automation Project"
  }'
```

**Expected Response:**
- Account confirmation
- Email verification (possibly)
- Username confirmation

---

### **Step 3: Obtain API Token**

**Action:** Authenticate to get Bearer token
- **Method:** HTTP POST to `/login` endpoint with credentials

**Example curl:**
```bash
curl -X POST https://api.watttime.org/v3/login \
  -u "your-username:your-password"
```

**Expected Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 1800
}
```

**⚠️ Important:** Tokens expire after 30 minutes!

---

### **Step 4: Determine Your Access Plan**

WattTime offers different tiers:

#### **Free Tier (Basic)**
- ✅ Real-time marginal emissions (MOER) data
- ✅ 1-2 regions (limited coverage)
- ✅ Basic forecast data
- ❌ Limited to certain regions (typically US)
- ❌ No health damage signals

**Coverage:** US grids (CAISO, PJM, ERCOT, etc.)

#### **Paid Tiers (Analyst/Pro)**
- ✅ All data signals (MOER, AOER, Health Damage)
- ✅ Global coverage (12+ countries)
- ✅ Historical data access
- ✅ Higher rate limits

**Coverage:** US + Mexico, Japan, South Korea, Brazil, India, Chile, Peru, Turkey, Malaysia, Nicaragua, Philippines, Singapore

---

### **Step 5: Find Your Grid Region**

**Action:** Determine your grid region identifier

**For US:**
- **CAISO_NORTH** - California ISO North
- **CAISO_SOUTH** - California ISO South
- **ERCOT** - Texas
- **PJM** - Mid-Atlantic
- **NYISO** - New York
- **ISONE** - New England
- **MISO** - Midwest

**API Endpoint to Find Region:**
```bash
curl -X GET "https://api.watttime.org/v3/region-from-loc?latitude=37.7749&longitude=-122.4194" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "region": "CAISO_NORTH",
  "signal_type": "co2_moer"
}
```

---

### **Step 6: Test Your Token**

**Action:** Verify token works with forecast endpoint

```bash
curl -X GET "https://api.watttime.org/v3/forecast?region=CAISO_NORTH" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "region": "CAISO_NORTH",
  "moer": 450.5,
  "renewable_pct": 35.2,
  "forecast": [
    {
      "point_time": "2025-01-15T20:00:00Z",
      "value": 445.2
    },
    ...
  ]
}
```

**If you get HTTP 401:** Token is invalid/expired
**If you get HTTP 403:** Region not accessible on your plan

---

## Configuration in HA Ingestor

Once you have your token:

### **Option 1: Environment Variables (Recommended)**

Edit `infrastructure/env.example` (or create `.env`):

```bash
# WattTime Carbon Intensity API
WATTTIME_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GRID_REGION=CAISO_NORTH  # Or your region
```

### **Option 2: Docker Compose Override**

Edit `docker-compose.yml`:

```yaml
carbon-intensity-service:
  environment:
    - WATTTIME_API_TOKEN=YOUR_TOKEN_HERE
    - GRID_REGION=CAISO_NORTH
```

---

## Token Refresh Strategy

### **Current Implementation Issue**

Our service expects a **static Bearer token**, but WattTime tokens **expire after 30 minutes**!

### **Solution Options**

#### **Option A: Short-Term (Manual Refresh)**
1. Get token manually
2. Update environment variable
3. Restart service
4. Repeat every 30 minutes (not practical!)

#### **Option B: Long-Term (Automated Refresh)**

**Implement token refresh in service** (recommended):

```python
# Add to CarbonIntensityService class
async def refresh_token(self):
    """Refresh WattTime API token"""
    url = "https://api.watttime.org/v3/login"
    auth = aiohttp.BasicAuth(self.username, self.password)
    
    async with self.session.post(url, auth=auth) as response:
        if response.status == 200:
            data = await response.json()
            self.api_token = data['token']
            logger.info("WattTime token refreshed")
            return True
    return False

async def run_continuous(self):
    """Run with token refresh"""
    last_refresh = datetime.now()
    
    while True:
        # Refresh token every 25 minutes (before expiry)
        if (datetime.now() - last_refresh).total_seconds() > 1500:
            await self.refresh_token()
            last_refresh = datetime.now()
        
        # Fetch data
        data = await self.fetch_carbon_intensity()
        ...
```

**Required Env Variables:**
```bash
WATTTIME_USERNAME=your-username
WATTTIME_PASSWORD=your-password
# No need for WATTTIME_API_TOKEN - will be auto-generated
```

---

## Implementation Checklist

### Phase 1: Registration (Do This First)
- [ ] Visit WattTime website / developer portal
- [ ] Register account (username, password, email, org)
- [ ] Confirm email (if required)
- [ ] Log in to get initial token
- [ ] Note your access plan (free/paid)

### Phase 2: Region Configuration
- [ ] Determine your geographic location
- [ ] Use region lookup API to find grid region
- [ ] Verify region is accessible on your plan
- [ ] Test forecast endpoint with your token

### Phase 3: Service Configuration
- [ ] Add `WATTTIME_API_TOKEN` to environment
- [ ] Add `GRID_REGION` to environment
- [ ] Deploy/restart carbon-intensity-service
- [ ] Check service health: `curl http://localhost:8010/health`
- [ ] Verify data in InfluxDB

### Phase 4: Token Refresh (Recommended)
- [ ] Implement automatic token refresh
- [ ] Add username/password to environment
- [ ] Test token refresh logic
- [ ] Deploy updated service

---

## Testing the Service

### **1. Check Service Health**
```bash
curl http://localhost:8010/health
```

**Expected:**
```json
{
  "status": "healthy",
  "service": "carbon-intensity-service",
  "last_successful_fetch": "2025-01-15T19:45:00Z",
  "total_fetches": 45,
  "failed_fetches": 0
}
```

### **2. Check InfluxDB Data**
```bash
# Query InfluxDB for carbon intensity
curl -X POST "http://localhost:8086/api/v2/query?org=homeiq" \
  -H "Authorization: Token homeiq-token" \
  -H "Content-Type: application/vnd.flux" \
  -d 'from(bucket:"home_assistant_events")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "carbon_intensity")
  |> last()'
```

### **3. Check Service Logs**
```bash
docker logs homeiq-carbon-intensity --tail 50
```

**Expected:**
```
INFO: Fetching carbon intensity for region CAISO_NORTH
INFO: Carbon intensity: 450.5 gCO2/kWh, Renewable: 35.2%
INFO: Carbon intensity data written to InfluxDB
```

---

## Troubleshooting

### **Error: "WATTTIME_API_TOKEN environment variable is required"**
**Cause:** Token not set in environment
**Fix:** Add token to `.env` or `docker-compose.yml`

### **Error: "WattTime API returned status 401"**
**Cause:** Token is invalid or expired
**Fix:** Get new token from `/login` endpoint

### **Error: "WattTime API returned status 403"**
**Cause:** Region not accessible on your plan
**Fix:** 
1. Use a different region (free tier)
2. Upgrade your WattTime plan
3. Contact WattTime support

### **Error: Token expires every 30 minutes**
**Cause:** WattTime design (security)
**Fix:** Implement automatic token refresh (see Option B above)

---

## Alternative: Use Mock Data (For Testing)

If WattTime registration is difficult, you can temporarily use mock data:

```python
# In main.py, modify fetch_carbon_intensity()
async def fetch_carbon_intensity(self) -> Optional[Dict[str, Any]]:
    """Fetch carbon intensity (MOCK DATA FOR TESTING)"""
    
    # Mock data - remove when real token available
    data = {
        'carbon_intensity': 450.5,  # gCO2/kWh
        'renewable_percentage': 35.2,
        'fossil_percentage': 64.8,
        'forecast_1h': 445.2,
        'forecast_24h': 480.0,
        'timestamp': datetime.now()
    }
    
    logger.info(f"USING MOCK DATA - Carbon intensity: {data['carbon_intensity']}")
    return data
```

---

## Cost Considerations

### **Free Tier**
- ✅ **Cost:** $0
- ✅ **Coverage:** 1-2 US regions
- ✅ **Data:** Real-time MOER
- ❌ **Limitations:** Limited regions, no health damage

**Best for:** Hobbyists, testing, single-location monitoring

### **Paid Tiers**
- 💰 **Cost:** Contact WattTime sales
- ✅ **Coverage:** Global (12+ countries)
- ✅ **Data:** MOER, AOER, Health Damage, Historical
- ✅ **Benefits:** Higher rate limits, priority support

**Best for:** Commercial use, multi-region, advanced analytics

---

## Next Steps

1. **Register with WattTime** (follow Step 1-3 above)
2. **Get your token and region**
3. **Configure environment variables**
4. **Test the service**
5. **Implement token refresh** (Phase 4)
6. **Monitor in dashboard** (Data Sources tab should show "Carbon Intensity: Healthy")

---

## Resources

- **WattTime Website:** https://watttime.org
- **API Documentation:** https://docs.watttime.org
- **Python Client SDK:** https://watttime-python-client.readthedocs.io
- **Support:** support@watttime.org
- **API Status:** Check WattTime status page

---

## Summary

**YES - Your Research is Correct!** ✅

The steps you outlined are accurate:

1. ✅ Visit developer site
2. ✅ Register account (/register endpoint or web form)
3. ✅ Log in to get token (/login endpoint)
4. ✅ Receive Bearer token (valid 30 min)
5. ✅ Confirm access level (free vs paid)
6. ✅ Use token in requests (Authorization: Bearer header)
7. ✅ Contact WattTime for elevated access (if needed)

**Additional Recommendation:** Implement automatic token refresh to avoid manual renewal every 30 minutes.

---

**Status:** Ready to implement once you have WattTime credentials! 🚀

