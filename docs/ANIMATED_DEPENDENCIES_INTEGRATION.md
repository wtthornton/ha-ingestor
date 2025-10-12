# Animated Real-Time Dependencies Tab - Integration Guide

## 🌊 Overview

This guide shows how to integrate the **animated, real-time data flow visualization** into the Dependencies tab. Data flows like water through your system with smooth animations, pulsing particles, and real-time metrics!

**Research Foundation:**
- ✅ Context7 KB: React Flow (/websites/reactflow_dev) - Animated edges & custom visualizations
- ✅ Context7 KB: Framer Motion (/grx7/framer-motion) - Smooth SVG animations
- ✅ Web Research: Real-time dashboard best practices

---

## 🎨 Features

###  1. **Animated Data Particles**
- Particles flow along connection paths showing real-time data movement
- Speed varies based on throughput (faster = more data)
- Color-coded by data type:
  - 🔵 Blue = WebSocket connections
  - 🟢 Green = API calls
  - 🟣 Purple = Storage operations  
  - 🟠 Orange = Sports data

### 2. **Pulsing Effects**
- Nodes pulse when actively processing data
- Connections glow when data is flowing
- Status indicators animate continuously

### 3. **Real-Time Metrics**
- Events per second displayed live
- Active API count updates
- Throughput shown on connections
- Last update timestamp

### 4. **Interactive Features**
- Click nodes to highlight their connections
- Hover for detailed information
- Smooth zoom and pan (future)
- Filter by data type (future)

### 5. **Sports Integration**
- NFL/NHL API nodes shown separately
- Sports data flows highlighted in orange
- Team selection impacts which flows are active
- API call visualization for selected teams only

---

## 🚀 Quick Integration

### Step 1: Update Dashboard Component

```typescript
// services/health-dashboard/src/components/Dashboard.tsx

import { AnimatedDependencyGraph } from './AnimatedDependencyGraph';

// Add state for real-time metrics
const [realTimeMetrics, setRealTimeMetrics] = useState({
  eventsPerSecond: 0,
  apiCallsActive: 0,
  dataSourcesActive: [],
  lastUpdate: new Date(),
});

// Add polling for real-time data
useEffect(() => {
  const fetchRealTimeMetrics = async () => {
    try {
      const response = await fetch('/api/v1/metrics/realtime');
      const data = await response.json();
      setRealTimeMetrics({
        eventsPerSecond: data.events_per_second || 0,
        apiCallsActive: data.active_api_calls || 0,
        dataSourcesActive: data.active_sources || [],
        lastUpdate: new Date(),
      });
    } catch (err) {
      console.error('Failed to fetch real-time metrics:', err);
    }
  };

  // Initial fetch
  fetchRealTimeMetrics();

  // Poll every 2 seconds for real-time feel
  const interval = setInterval(fetchRealTimeMetrics, 2000);

  return () => clearInterval(interval);
}, []);

// In your render, replace ServiceDependencyGraph with AnimatedDependencyGraph
{selectedTab === 'dependencies' && (
  <AnimatedDependencyGraph
    services={services}
    darkMode={darkMode}
    realTimeData={realTimeMetrics}
  />
)}
```

### Step 2: Add Real-Time Metrics API Endpoint

```python
# services/admin-api/src/main.py

@app.get("/api/v1/metrics/realtime")
async def get_realtime_metrics():
    """Get real-time metrics for data flow visualization"""
    
    # Calculate events per second from recent data
    recent_events = await get_recent_event_count(seconds=5)
    events_per_second = recent_events / 5.0
    
    # Count active API integrations
    active_apis = []
    
    # Check NFL API
    if await is_source_active('nfl'):
        active_apis.append('nfl')
    
    # Check NHL API
    if await is_source_active('nhl'):
        active_apis.append('nhl')
    
    # Check Weather API
    if await is_source_active('weather'):
        active_apis.append('weather')
    
    return {
        "events_per_second": round(events_per_second, 2),
        "active_api_calls": len(active_apis),
        "active_sources": active_apis,
        "timestamp": datetime.utcnow().isoformat()
    }

async def is_source_active(source: str) -> bool:
    """Check if a data source is actively sending data"""
    # Check if we've received data from this source in last 60 seconds
    recent_data = await check_recent_data(source, seconds=60)
    return recent_data > 0
```

### Step 3: Update Nginx Config (if needed)

```nginx
# services/health-dashboard/nginx.conf

location /api/v1/metrics/realtime {
    proxy_pass http://admin-api:8004/api/v1/metrics/realtime;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    
    # Short cache for real-time data
    proxy_cache_valid 200 2s;
}
```

---

## 🎯 Visual Examples

### Basic Flow Visualization

```
┌─────────────────────────────────────────────────────────┐
│  Real-Time Data Flow Visualization        42.5/s  3 APIs│
├─────────────────────────────────────────────────────────┤
│                                                           │
│          🏈 NFL API    🏒 NHL API    🏠 Home Assistant   │
│                 ↓            ↓              ↓            │
│            ●●●●●●●      ●●●●●●●        ●●●●●●●●●●       │
│                 ↘            ↓              ↙             │
│              ⚡ Sports Data    📡 WebSocket Ingestion    │
│                      ↘          ↙                         │
│                   ●●●●●●●●●●●●●●                         │
│                          ↓                                │
│                  🔄 Enrichment Pipeline                   │
│                    ↙       ↓        ↘                    │
│             🗄️ InfluxDB  🔌 Admin API  📊 Dashboard      │
│                                                           │
│  Legend: ● = Data particles  |  ●●● = Active flow       │
└─────────────────────────────────────────────────────────┘
```

### With Sports Teams Selected

When user selects Dallas Cowboys and Boston Bruins:

```
Active Flows:
✅ NFL API → Sports Data (Dallas Cowboys games)
✅ NHL API → Sports Data (Boston Bruins games)
✅ Sports Data → Enrichment Pipeline
✅ Home Assistant → WebSocket Ingestion
✅ Enrichment Pipeline → InfluxDB

Inactive:
❌ Other teams' data not flowing (not selected)
```

---

## 🔧 Advanced Features

### Feature 1: Filter by Team Selection

```typescript
// In AnimatedDependencyGraph.tsx, add team filter
interface AnimatedDependencyGraphProps {
  services: ServiceStatus[];
  darkMode: boolean;
  realTimeData?: RealTimeMetrics;
  selectedTeams?: string[]; // NEW: Filter flows by team
}

// Update data flows based on selected teams
const getActiveFlows = () => {
  if (!selectedTeams || selectedTeams.length === 0) {
    // No teams selected = show minimal flows
    return dataFlows.filter(f => 
      !f.id.includes('nfl') && !f.id.includes('nhl')
    );
  }
  
  // Show flows for selected teams
  const hasNFL = selectedTeams.some(t => t.startsWith('nfl-'));
  const hasNHL = selectedTeams.some(t => t.startsWith('nhl-'));
  
  return dataFlows.map(f => ({
    ...f,
    active: f.active && (
      !f.id.includes('nfl') && !f.id.includes('nhl') ||
      (f.id.includes('nfl') && hasNFL) ||
      (f.id.includes('nhl') && hasNHL)
    )
  }));
};
```

### Feature 2: Show Team-Specific Nodes

```typescript
// Dynamically show team nodes when selected
const getDynamicNodes = (): ServiceNode[] => {
  const baseNodes = [...nodes];
  
  // Add nodes for each selected team
  if (selectedTeams) {
    selectedTeams.forEach((teamId, index) => {
      const team = getTeamInfo(teamId);
      baseNodes.push({
        id: teamId,
        name: team.name,
        icon: team.league === 'NFL' ? '🏈' : '🏒',
        type: 'external',
        position: {
          x: 100 + (index * 80),
          y: 100
        }
      });
    });
  }
  
  return baseNodes;
};
```

### Feature 3: Throughput Heat Map

```typescript
// Color flows by throughput intensity
const getFlowColor = (throughput: number): string => {
  if (throughput > 100) return '#EF4444'; // Red hot
  if (throughput > 50) return '#F59E0B';  // Orange warm
  if (throughput > 10) return '#10B981';  // Green active
  return '#3B82F6'; // Blue idle
};

// Update path rendering
<path
  d={path}
  fill="none"
  stroke={getFlowColor(flow.throughput || 0)}
  strokeWidth={Math.min(5, 2 + (flow.throughput || 0) / 20)}
  opacity="0.8"
/>
```

### Feature 4: Performance Stats Overlay

```typescript
// Add stats panel
<div className={`absolute top-4 right-4 p-4 rounded-lg ${
  darkMode ? 'bg-gray-900/90' : 'bg-white/90'
} backdrop-blur`}>
  <h4 className="font-bold mb-2">System Performance</h4>
  <div className="space-y-1 text-sm">
    <div>Total Throughput: {totalThroughput.toFixed(1)}/s</div>
    <div>Active Connections: {activeConnections}</div>
    <div>Avg Latency: {avgLatency.toFixed(0)}ms</div>
    <div>Error Rate: {errorRate.toFixed(2)}%</div>
  </div>
</div>
```

---

## 📊 Sports Integration Specifics

### Showing Sports Data Flows

```typescript
// Add sports-specific nodes and flows
const sportsNodes: ServiceNode[] = [
  {
    id: 'nfl-espn',
    name: 'ESPN NFL',
    icon: '🏈',
    type: 'external',
    position: { x: 50, y: 50 },
    metrics: {
      throughput: espnNFLCalls,
      latency: espnNFLLatency,
      errorRate: espnNFLErrors
    }
  },
  {
    id: 'nhl-official',
    name: 'NHL API',
    icon: '🏒',
    type: 'external',
    position: { x: 150, y: 50 },
    metrics: {
      throughput: nhlAPICalls,
      latency: nhlAPILatency,
      errorRate: nhlAPIErrors
    }
  }
];

// Sports-specific data flows
const sportsFlows: DataFlowPath[] = [
  {
    id: 'nfl-live-games',
    from: 'nfl-espn',
    to: 'sports-data',
    type: 'api',
    active: hasLiveNFLGames,
    throughput: nflGameUpdatesPerSecond,
    color: '#FF6B00' // NFL orange
  },
  {
    id: 'nhl-live-games',
    from: 'nhl-official',
    to: 'sports-data',
    type: 'api',
    active: hasLiveNHLGames,
    throughput: nhlGameUpdatesPerSecond,
    color: '#0033A0' // NHL blue
  }
];
```

### Live Game Indicators

```typescript
// Show special indicators for live games
{hasLiveGames && (
  <g>
    <circle
      cx={sportsDataNode.position.x}
      cy={sportsDataNode.position.y}
      r="40"
      fill="none"
      stroke="#FF0000"
      strokeWidth="2"
      opacity="0.6"
    >
      <animate
        attributeName="r"
        values="40;50;40"
        dur="1s"
        repeatCount="indefinite"
      />
      <animate
        attributeName="opacity"
        values="0.6;0.2;0.6"
        dur="1s"
        repeatCount="indefinite"
      />
    </circle>
    <text
      x={sportsDataNode.position.x}
      y={sportsDataNode.position.y - 60}
      textAnchor="middle"
      fill="#FF0000"
      fontSize="14"
      fontWeight="bold"
    >
      🔴 {liveGameCount} LIVE
    </text>
  </g>
)}
```

---

## 🎭 Animation Details

### SVG Animation Techniques Used

1. **`<animateMotion>`** - Moves particles along paths
   ```svg
   <circle r="4" fill="#3B82F6">
     <animateMotion dur="2s" repeatCount="indefinite" path={edgePath} />
   </circle>
   ```

2. **`<animate>`** - Animates attributes like radius, opacity
   ```svg
   <circle r="30">
     <animate attributeName="r" values="30;35;30" dur="2s" />
   </circle>
   ```

3. **CSS Transitions** - Smooth hover effects
   ```typescript
   style={{ 
     cursor: 'pointer',
     transition: 'all 0.3s ease',
   }}
   ```

4. **Filter Effects** - Glow and blur
   ```svg
   <filter id="glow">
     <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
     <feMerge>
       <feMergeNode in="coloredBlur"/>
       <feMergeNode in="SourceGraphic"/>
     </feMerge>
   </filter>
   ```

### Performance Optimizations

1. **Request Animation Frame** - Smooth 60fps updates
2. **SVG over Canvas** - Better for interactive elements
3. **Conditional Rendering** - Only animate visible particles
4. **Debounced Updates** - Throttle real-time data updates to 2s
5. **CSS Will-Change** - Hint browser for optimizations

---

## 🧪 Testing

### E2E Test for Animated Dependencies

```typescript
// services/health-dashboard/tests/e2e/animated-dependencies.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Animated Dependencies Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
    await page.click('button:has-text("🔗 Dependencies")');
  });

  test('should show animated data flows', async ({ page }) => {
    // Check for SVG container
    const svg = page.locator('svg');
    await expect(svg).toBeVisible();

    // Check for animated particles
    const particles = svg.locator('circle[r="4"]');
    await expect(particles.first()).toBeVisible();

    // Verify animations are running
    const animateMotion = svg.locator('animateMotion');
    await expect(animateMotion.first()).toBeAttached();
  });

  test('should show real-time metrics', async ({ page }) => {
    await expect(page.locator('text=events/sec')).toBeVisible();
    await expect(page.locator('text=active APIs')).toBeVisible();
  });

  test('should highlight connections on node click', async ({ page }) => {
    // Click a node
    await page.click('text=Enrichment Pipeline');

    // Verify highlight appears
    await expect(page.locator('text=Clear Selection')).toBeVisible();
    
    // Check connection count is shown
    await expect(page.locator('text=/Connections:/')).toBeVisible();
  });

  test('should show sports data flows when teams selected', async ({ page }) => {
    // This would require sports tab to be implemented
    // Navigate to sports config
    await page.click('button:has-text("⚙️ Configuration")');
    
    // Select teams
    // ... team selection logic ...
    
    // Go back to dependencies
    await page.click('button:has-text("🔗 Dependencies")');
    
    // Verify sports flows are active
    await expect(page.locator('text=NFL API')).toBeVisible();
    await expect(page.locator('text=NHL API')).toBeVisible();
  });
});
```

---

## 📱 Mobile Responsive

```typescript
// Add responsive breakpoints
const isMobile = window.innerWidth < 768;

<svg
  width={isMobile ? "100%" : "800"}
  height={isMobile ? "400" : "600"}
  viewBox={isMobile ? "0 0 400 300" : "0 0 800 600"}
  preserveAspectRatio="xMidYMid meet"
>
```

---

## 🎨 Theme Customization

```typescript
// Add custom themes
const themes = {
  default: {
    websocket: '#3B82F6',
    api: '#10B981',
    storage: '#8B5CF6',
    sports: '#F59E0B'
  },
  cyberpunk: {
    websocket: '#00FFF0',
    api: '#FF00FF',
    storage: '#00FF00',
    sports: '#FFFF00'
  },
  ocean: {
    websocket: '#0EA5E9',
    api: '#06B6D4',
    storage: '#3B82F6',
    sports: '#8B5CF6'
  }
};
```

---

## 🚀 Deployment Checklist

- [ ] Add `AnimatedDependencyGraph` component to Dashboard
- [ ] Implement `/api/v1/metrics/realtime` endpoint
- [ ] Update Nginx proxy config
- [ ] Add real-time metrics polling
- [ ] Test animations in different browsers
- [ ] Verify performance (should be 60fps)
- [ ] Add E2E tests
- [ ] Update documentation
- [ ] Test on mobile devices
- [ ] Verify sports integration flows

---

## 📚 Resources

- [React Flow Documentation](https://reactflow.dev/)
- [SVG Animation Tutorial](https://developer.mozilla.org/en-US/docs/Web/SVG/Element/animate)
- [Framer Motion Guide](https://www.framer.com/motion/)
- [Real-Time Dashboard Best Practices](https://www.patterns.dev/posts/real-time-dashboard)

---

## 🎉 Expected Impact

**Before:**
- Static dependency graph
- No real-time updates
- Click to see connections
- No throughput visualization

**After:**
- 🌊 Flowing data particles
- 📊 Real-time metrics (2s updates)
- ⚡ Interactive highlights
- 📈 Throughput visualization
- 🎨 Beautiful animations
- 🏈🏒 Sports integration visible

**User Delight Factor:** 10/10! 🚀

---

*Integration Guide v1.0*  
*Created: October 12, 2025*  
*Powered by Context7 KB Research*

