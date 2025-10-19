# AI Automation UI

**Conversational automation suggestion refinement interface for Home Assistant**

## Overview

The AI Automation UI provides a user-friendly, conversational interface for reviewing, refining, and deploying AI-generated automation suggestions. Built on **Story AI1.23-24** (Conversational Suggestion Refinement), it replaces the traditional YAML-first approach with a description-first workflow.

### Key Features

- 💬 **Conversational Refinement** - Edit suggestions with natural language ("make it 6:30am instead")
- 📝 **Description-First** - See automation ideas in plain English before any code
- ✅ **YAML on Approval** - Code only generated after you approve the description
- 🚀 **One-Click Deploy** - Push approved automations directly to Home Assistant
- 🎨 **Beautiful UI** - Modern, responsive design with dark mode support
- ⚡ **Real-Time Updates** - WebSocket integration for live status

## Quick Start

### Running with Docker (Recommended)

```bash
# From project root
docker-compose up -d ai-automation-ui

# Access UI
open http://localhost:3001
```

### Running Locally (Development)

```bash
cd services/ai-automation-ui

# Install dependencies
npm install

# Start dev server
npm run dev

# Access UI
open http://localhost:3001
```

## User Interface

### Main Dashboard (ConversationalDashboard)

The main interface displays suggestions in a card-based layout with status tabs:

- **📝 Draft** - New suggestions (description only, no YAML yet)
- **✏️ Refining** - Suggestions you're editing
- **✅ Ready** - Approved suggestions with generated YAML
- **🚀 Deployed** - Automations running in Home Assistant

### Conversational Flow

```
1. View Draft Suggestion
   └─> "Turn on office lights at 7:00am every morning"
   
2. Click "Refine" (Optional)
   └─> Type: "Make it 6:30am instead"
   └─> AI updates: "Turn on office lights at 6:30am every morning"
   └─> Type: "And only on weekdays"
   └─> AI updates: "Turn on office lights at 6:30am on weekdays"
   
3. Click "Approve"
   └─> AI generates Home Assistant YAML
   └─> Shows automation code
   └─> Status changes to "Ready"
   
4. Click "Deploy"
   └─> Pushes to Home Assistant
   └─> Status changes to "Deployed"
```

## Pages & Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | ConversationalDashboard | Main suggestion feed (description-first) |
| `/patterns` | Patterns | View detected patterns |
| `/synergies` | Synergies | Cross-automation opportunities |
| `/deployed` | Deployed | Active automations in HA |
| `/discovery` | Discovery | Device exploration |
| `/settings` | Settings | UI preferences & configuration |

## Architecture

### Status States (Story AI1.23)

```
draft → refining → yaml_generated → deployed
  ↓                      ↓
rejected            rejected
```

**Status Definitions:**
- `draft` - New suggestion, description only, no YAML
- `refining` - User is editing with conversational AI
- `yaml_generated` - User approved, YAML created, ready to deploy
- `deployed` - Automation active in Home Assistant
- `rejected` - User rejected the suggestion

### API Integration

**Backend:** `ai-automation-service` (port 8018)

**Key Endpoints:**
- `GET /api/suggestions/list?status=draft` - Load suggestions
- `POST /api/v1/suggestions/{id}/refine` - Conversational editing
- `POST /api/v1/suggestions/{id}/approve` - Generate YAML
- `POST /api/deploy/{id}` - Deploy to Home Assistant

## Components

### ConversationalSuggestionCard

Main card component for displaying suggestions with:
- Description display (collapsible)
- Refinement input (inline editing)
- Action buttons (Refine, Approve, Deploy, Reject)
- YAML code block (only shown after approval)
- Confidence meter
- Category badges

### Key Features:
- **Inline Editing**: Click "Refine" to edit without modal
- **Optimistic Updates**: UI updates immediately, API call in background
- **Error Handling**: Graceful fallbacks if API fails
- **Accessibility**: ARIA labels, keyboard navigation

## Tech Stack

- **Framework**: React 18.2.0 with TypeScript 5.2.2
- **State Management**: Zustand 4.4.7
- **Styling**: TailwindCSS 3.4.0
- **Routing**: React Router DOM 6.20.0
- **Animations**: Framer Motion 10.16.16
- **Charts**: Chart.js 4.4.1 + React-ChartJS-2 5.2.0
- **Notifications**: React Hot Toast 2.4.1
- **Build Tool**: Vite 5.0.8

## Development

### File Structure

```
src/
├── pages/
│   └── ConversationalDashboard.tsx  # Main dashboard (root route)
├── components/
│   ├── ConversationalSuggestionCard.tsx  # Suggestion card
│   ├── Navigation.tsx  # Top navigation
│   └── CustomToast.tsx  # Toast notifications
├── services/
│   └── api.ts  # API client
├── store.ts  # Zustand global state
├── types/
│   └── index.ts  # TypeScript types
└── App.tsx  # Routes & layout
```

### State Management

**Zustand Store (`store.ts`):**
- `suggestions` - Array of automation suggestions
- `selectedStatus` - Current status filter (draft/refining/yaml_generated/deployed)
- `darkMode` - UI theme preference
- `scheduleInfo` - Analysis job status

### Environment Variables

```env
# Development (services/ai-automation-ui/.env.development)
VITE_API_URL=http://localhost:8018/api

# Production (Docker)
# nginx proxies /api to http://ai-automation-service:8018/api
```

## Building & Deployment

### Docker Build

```dockerfile
# Multi-stage build
FROM node:18-alpine AS deps
# ... install dependencies

FROM node:18-alpine AS builder
# ... build production bundle
RUN npm run build

FROM nginx:alpine AS production
# ... serve static files
```

### Production Deployment

```bash
# Build and start
docker-compose up -d --build ai-automation-ui

# Check status
docker ps | grep ai-automation-ui

# View logs
docker logs ai-automation-ui -f
```

## Testing

### Manual Testing

1. **View Draft Suggestions:**
   - Navigate to http://localhost:3001/
   - Should see suggestions with descriptions only
   - No YAML code visible

2. **Test Refinement:**
   - Click "Refine" on any draft suggestion
   - Type: "change the time to 8am"
   - Verify description updates

3. **Test Approval:**
   - Click "Approve" on refined suggestion
   - Verify YAML code appears
   - Verify status changes to "Ready"

4. **Test Deployment:**
   - Click "Deploy" on ready suggestion
   - Check Home Assistant for new automation
   - Verify status changes to "Deployed"

## Troubleshooting

### "No Draft Suggestions"

**Cause:** New suggestions not yet generated or old data has YAML  
**Fix:** Trigger new analysis:
```bash
curl -X POST http://localhost:8018/api/analysis/trigger
```

### "API Connection Failed"

**Cause:** Backend service not running  
**Fix:** Check backend status:
```bash
docker ps | grep ai-automation-service
docker logs ai-automation-service
```

### "YAML Appears in Draft"

**Cause:** Old suggestions created before Story AI1.24  
**Fix:** Delete old suggestions or run database migration:
```sql
UPDATE suggestions 
SET automation_yaml = NULL, yaml_generated_at = NULL
WHERE status = 'draft';
```

## Related Documentation

- **Backend Service:** `services/ai-automation-service/README.md`
- **Story AI1.23:** `docs/stories/story-ai1-23-conversational-refinement.md`
- **Story AI1.24:** `docs/stories/story-ai1-24-conversational-ui-cleanup.md`
- **Implementation:** `implementation/PHASE_2_BACKEND_CLEANUP_COMPLETE.md`
- **Call Tree:** `implementation/analysis/AI_AUTOMATION_CALL_TREE_INDEX.md`

---

**Version:** 2.0.0  
**Story:** AI1.24 - Conversational UI (Description-First Flow)  
**Status:** ✅ Production Ready  
**Port:** 3001

