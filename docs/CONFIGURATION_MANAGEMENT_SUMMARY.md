# Configuration Management - Quick Summary

## 🎯 Goal
Simple web UI to manage external API tokens and control services. No over-engineering.

---

## ✅ What You Get

### 1. Configuration UI
- Edit Home Assistant token & URL
- Edit Weather API key & location
- Edit InfluxDB credentials
- Edit other service configs
- Masked passwords/tokens (••••••)

### 2. Service Control
- View service status (running/stopped)
- Restart button for each service
- Restart all button
- Simple, clear UI

---

## 🏗️ How It Works

```
Edit Config → Save to .env File → Restart Service → Done
```

**Simple!** No database, no encryption complexity, no hot-reload.

---

## 💻 Implementation

### Backend (FastAPI)
```python
# 3 simple endpoints:
GET  /api/config/{service}           # Read .env file
PUT  /api/config/{service}           # Write .env file
POST /api/services/{service}/restart # Restart Docker container
```

### Frontend (React)
```typescript
<ConfigForm service="websocket" />
  ├─ Input fields for each setting
  ├─ Save button
  └─ Restart button
```

### Configuration Files
```bash
infrastructure/
├── .env.websocket  # Home Assistant
├── .env.weather    # Weather API
├── .env.influxdb   # Database
└── .env.example    # Template
```

---

## 📅 Timeline

### Week 1: Backend (2-3 days)
- .env file reader/writer
- Service restart endpoint
- Basic validation

### Week 2: Frontend (2-3 days)
- Config form component
- Service control component
- Add to dashboard

### Week 3: Polish (1-2 days)
- All services added
- Error handling
- Documentation

**Total: 5-8 days**

---

## 🎨 UI Preview

```
┌──────────────────────────────────────────┐
│  🏠 Home Assistant                       │
│  ├─ URL:   [ws://192.168.1.100:8123...] │
│  ├─ Token: [••••••••5678] [Show]        │
│  └─ [Save] [Restart]                    │
│                                          │
│  ☁️ Weather API                          │
│  ├─ Key:   [••••••••abcd] [Show]        │
│  ├─ Lat:   [51.5074]                    │
│  ├─ Lon:   [-0.1278]                    │
│  └─ [Save] [Restart]                    │
└──────────────────────────────────────────┘
```

---

## 🔒 Security

### Simple & Effective
- .env files with `chmod 600` (owner only)
- Masked tokens in UI (click Show to reveal)
- No complex encryption needed
- File permissions handle security

---

## 🚫 What We're NOT Doing

Keep it simple:
- ❌ No database
- ❌ No complex encryption
- ❌ No hot-reload
- ❌ No JWT/OAuth
- ❌ No version control
- ❌ No audit logs

---

## 🎯 Services to Configure

### Start With (Phase 1)
1. Home Assistant (WebSocket URL + Token)
2. Weather API (API Key + Location)
3. InfluxDB (URL + Token + Org + Bucket)

### Add Later (Phase 2)
4. Carbon Intensity
5. Electricity Pricing
6. Air Quality
7. Calendar (if needed)
8. Smart Meter (if needed)

---

## 📝 User Workflow

1. Open dashboard
2. Click "Configuration" page
3. Select service to edit
4. Update values (API keys, URLs)
5. Click "Save"
6. Click "Restart Service"
7. Done!

**Takes < 30 seconds to update any config**

---

## ✅ Success Criteria

- [ ] Edit configs through UI (no file editing)
- [ ] Restart services with button click
- [ ] API keys masked for security
- [ ] Changes persist after restart
- [ ] Clear error messages
- [ ] Fast and simple to use

---

## 🚀 Ready to Start?

### Questions:
1. Start with just Home Assistant + Weather + InfluxDB?
2. Any other critical services?
3. Ready for me to implement?

---

**Full Details:** [SIMPLE_INTEGRATION_MANAGEMENT.md](SIMPLE_INTEGRATION_MANAGEMENT.md)  
**Research:** [Context7 KB: Simple Config Pattern](kb/context7-cache/simple-config-management-pattern.md)  
**Approach:** KISS (Keep It Simple, Stupid)  
**Timeline:** 5-8 days  
**Status:** ✅ Ready to implement

