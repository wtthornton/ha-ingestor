# Context7 Knowledge Base: Home Assistant Ingestion Layer

This document contains comprehensive technical documentation gathered from Context7 for all key technologies used in the Home Assistant Ingestion Layer project.

## Table of Contents

1. [aiohttp - Async HTTP/WebSocket Client](#aiohttp---async-httpwebsocket-client)
2. [InfluxDB - Time Series Database](#influxdb---time-series-database)
3. [Docker Compose - Container Orchestration](#docker-compose---container-orchestration)
4. [Home Assistant - WebSocket API](#home-assistant---websocket-api)
5. [TypeScript/React - Frontend Development](#typescriptreact---frontend-development)

---

## aiohttp - Async HTTP/WebSocket Client

### Overview
aiohttp is an asynchronous HTTP client/server framework for asyncio and Python, providing WebSocket support for real-time communication.

### Key Features
- **Async WebSocket Client**: Full WebSocket client support with async/await syntax
- **Connection Management**: Automatic connection handling with context managers
- **Message Types**: Support for TEXT, BINARY, JSON, PING/PONG messages
- **Error Handling**: Comprehensive error handling and connection state management

### WebSocket Client Usage

#### Basic Connection
```python
import aiohttp

async def connect_and_use_websocket(url):
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            await ws.send_str('Hello WebSocket!')
            msg = await ws.receive()
            print(f"Received message: {msg.data}")
```

#### Advanced WebSocket Configuration
```python
async with session.ws_connect(
    url,
    protocols=(), 
    timeout=aiohttp.ClientWSTimeout(ws_receive=None, ws_close=10.0),
    auth=None,
    autoclose=True,
    autoping=True,
    heartbeat=None,
    origin=None, 
    params=None, 
    headers=None, 
    proxy=None, 
    ssl=True, 
    verify_ssl=None,
    compress=0, 
    max_msg_size=4194304
) as ws:
    # WebSocket operations
    pass
```

#### Message Handling
```python
async with session.ws_connect('http://example.org/ws') as ws:
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close cmd':
                await ws.close()
                break
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            break
```

#### Sending Different Message Types
```python
# Send text message
await ws.send_str("Hello World")

# Send binary message
await ws.send_bytes(b"Binary data")

# Send JSON message
await ws.send_json({"key": "value"})

# Send ping/pong
await ws.ping("ping message")
await ws.pong("pong message")

# Close connection
await ws.close(code=WSCloseCode.OK, message=b'')
```

#### Receiving Messages
```python
# Receive any message
msg = await ws.receive()

# Receive specific message types
text_msg = await ws.receive_str()
binary_msg = await ws.receive_bytes()
json_msg = await ws.receive_json()
```

### Error Handling
```python
# Check for exceptions
if ws.exception():
    print(f"WebSocket error: {ws.exception()}")

# Handle different message types
if msg.type == aiohttp.WSMsgType.ERROR:
    print(f"WebSocket error: {msg.data}")
elif msg.type == aiohttp.WSMsgType.CLOSE:
    print("WebSocket closed")
```

---

## InfluxDB - Time Series Database

### Overview
InfluxDB is a database designed for collecting, processing, transforming, and storing time-series data, ideal for real-time monitoring and automation solutions.

### Key Features
- **Time Series Optimized**: Built specifically for timestamped data
- **High Performance**: Optimized for high write and query loads
- **Multiple Query Languages**: Supports SQL, InfluxQL, and Flux
- **Client Libraries**: Available for Python, Go, JavaScript, Java, C#

### Python Client Usage

#### Basic Setup
```python
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# Configuration
url = "http://localhost:8086"
token = "YOUR_INFLUXDB_TOKEN"
org = "YOUR_ORG"
bucket = "YOUR_BUCKET"

# Initialize client
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)
```

#### Writing Data Points
```python
# Create a point
point = Point("home") \
    .tag("room", "Living Room") \
    .field("temp", 23.5) \
    .field("hum", 45.2) \
    .field("co", 500) \
    .time(None, WritePrecision.NS)  # Use current time

# Write the point
write_api.write(bucket=bucket, org=org, record=point)
```

#### Writing Multiple Points
```python
# Create multiple points
points = [
    Point("home")
        .tag("room", "Living Room")
        .field("temp", 23.5)
        .field("hum", 45.2),
    Point("home")
        .tag("room", "Kitchen")
        .field("temp", 25.1)
        .field("hum", 48.0)
]

# Write all points
write_api.write(bucket=bucket, org=org, record=points)
```

#### Writing from Dictionary
```python
# Using dictionary structure
points = {
    "measurement": "home",
    "tags": {"room": "Kitchen", "sensor": "K001"},
    "fields": {"temp": 72.2, "hum": 36.9, "co": 4},
    "time": 1641067200
}

client.write(record=points, write_precision="s")
```

#### Querying Data
```python
# SQL query
query = '''
SELECT *
FROM home
WHERE time >= now() - INTERVAL '90 days'
ORDER BY time
'''

table = client.query(query=query, language="sql")
dataframe = table.to_pandas()
```

#### InfluxQL Query
```python
# InfluxQL query
query = '''
SELECT DISTINCT(temp) as val
FROM home
WHERE temp > 21.0
AND time >= now() - 10m
'''

table = client.query(query=query, language="influxql")
df = table.to_pandas()
```

#### Data Analysis with Pandas
```python
# Set time as index
dataframe = dataframe.set_index('time')

# Resample data by hour
resample = dataframe.resample("1H")

# Calculate mean temperature for each hour
hourly_avg = resample['temp'].mean()
```

#### Downsampling Data
```python
# SQL downsampling query
query = '''
SELECT
  DATE_BIN(INTERVAL '1 hour', time) AS time,
  room,
  AVG(temp) AS temp,
  AVG(hum) AS hum,
  AVG(co) AS co
FROM home
WHERE time >= now() - INTERVAL '24 hours'
GROUP BY 1, room
ORDER BY time
'''

table = client.query(query=query, language="sql")
data_frame = table.to_pandas()

# Write downsampled data back
data_frame = data_frame.sort_values(by="time")
client.write(
    record=data_frame,
    data_frame_measurement_name="home_ds",
    data_frame_timestamp_column="time",
    data_frame_tag_columns=['room']
)
```

### Best Practices
- **Batch Writes**: Write multiple points in batches for better performance
- **Proper Tagging**: Use tags for metadata that doesn't change frequently
- **Field Types**: Use appropriate field types (float, int, string, boolean)
- **Time Precision**: Choose appropriate time precision (ns, us, ms, s, m, h)
- **Retention Policies**: Set appropriate retention policies for data lifecycle

---

## Docker Compose - Container Orchestration

### Overview
Docker Compose is a tool for defining and running multi-container Docker applications using a Compose file format to configure application services.

### Key Features
- **Multi-Container Management**: Define and manage multiple services
- **Service Dependencies**: Handle service startup order and dependencies
- **Networking**: Automatic service discovery and networking
- **Volume Management**: Persistent data storage across containers
- **Environment Configuration**: Environment variables and configuration management

### Basic Usage

#### Starting Services
```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# Start specific service
docker compose up web
```

#### Service Management
```bash
# Stop services
docker compose down

# Restart services
docker compose restart

# View running containers
docker compose ps

# View all containers (including stopped)
docker compose ps --all
```

#### Building Services
```bash
# Build all services
docker compose build

# Build specific service
docker compose build web

# Build and start
docker compose up --build
```

### Compose File Structure

#### Basic Services Definition
```yaml
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - .:/code
  redis:
    image: redis
```

#### Advanced Service Configuration
```yaml
services:
  db:
    image: postgres
    environment:
      - POSTGRES_DB=myapp
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

  web:
    build: .
    command: bundle exec rails s -p 3000 -b '0.0.0.0'
    volumes:
      - .:/myapp
    ports:
      - "3000:3000"
    depends_on:
      - db
    environment:
      - DEBUG=1
    networks:
      - app-network

volumes:
  postgres_data:

networks:
  app-network:
    driver: bridge
```

#### Service Profiles
```yaml
services:
  web:
    image: nginx
    profiles:
      - frontend
  
  debug:
    image: debug-tools
    profiles:
      - debug
```

```bash
# Start specific profiles
docker compose --profile frontend up
docker compose --profile frontend --profile debug up
```

### Running Commands

#### Execute Commands in Services
```bash
# Run command in service
docker compose run web python manage.py shell

# Run with service ports
docker compose run --service-ports web python manage.py shell

# Run without dependencies
docker compose run --no-deps web python manage.py shell

# Run and remove container after
docker compose run --rm web python manage.py db upgrade
```

#### Interactive Shell
```bash
# Interactive shell
docker compose exec web sh

# Execute specific command
docker compose exec web python manage.py migrate
```

### Environment Configuration

#### Environment Variables
```bash
# Set environment variables
export COMPOSE_FILE=docker-compose.yml
export COMPOSE_PROJECT_NAME=my_project
export COMPOSE_PROFILES="frontend,debug"
export COMPOSE_PARALLEL_LIMIT=1
```

#### Multiple Compose Files
```bash
# Use multiple compose files
docker compose -f compose.yaml -f compose.admin.yaml up

# Override specific file
docker compose -f ~/sandbox/rails/compose.yaml pull db
```

### Monitoring and Debugging

#### View Logs
```bash
# View logs for all services
docker compose logs

# View logs for specific service
docker compose logs web

# Follow logs
docker compose logs -f web
```

#### View Processes
```bash
# View running processes
docker compose top
```

#### Events
```bash
# View events
docker compose events

# JSON output
docker compose events --json
```

### Best Practices
- **Use .env files**: Store sensitive configuration in .env files
- **Health Checks**: Implement health checks for services
- **Resource Limits**: Set appropriate resource limits
- **Security**: Use non-root users and minimal base images
- **Networking**: Use custom networks for service isolation
- **Volumes**: Use named volumes for persistent data

---

## Home Assistant - WebSocket API

### Overview
The Home Assistant WebSocket API provides real-time communication with Home Assistant instances, enabling event streaming and command execution.

### Key Features
- **Real-time Events**: Stream all Home Assistant events
- **Authentication**: Secure token-based authentication
- **Command Execution**: Execute Home Assistant commands
- **State Management**: Monitor and control entity states
- **Event Subscription**: Subscribe to specific event types

### Connection and Authentication

#### Basic Connection Flow
```python
import aiohttp
import json

async def connect_to_ha():
    url = "ws://homeassistant.local:8123/api/websocket"
    
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as ws:
            # 1. Receive auth_required
            auth_required = await ws.receive_json()
            print(f"Auth required: {auth_required}")
            
            # 2. Send authentication
            auth_msg = {
                "type": "auth",
                "access_token": "YOUR_LONG_LIVED_ACCESS_TOKEN"
            }
            await ws.send_json(auth_msg)
            
            # 3. Receive auth_ok
            auth_response = await ws.receive_json()
            print(f"Auth response: {auth_response}")
            
            # Now authenticated and ready to use
            return ws
```

#### Authentication Messages
```json
// Server sends auth_required
{
  "type": "auth_required",
  "ha_version": "2021.5.3"
}

// Client sends auth
{
  "type": "auth",
  "access_token": "ABCDEFGHIJKLMNOPQ"
}

// Server responds with auth_ok
{
  "type": "auth_ok",
  "ha_version": "2021.5.3"
}

// Or auth_invalid on failure
{
  "type": "auth_invalid",
  "message": "Invalid password"
}
```

### Event Subscription

#### Subscribe to All Events
```python
async def subscribe_to_events(ws):
    # Subscribe to all events
    subscribe_msg = {
        "id": 18,
        "type": "subscribe_events"
    }
    await ws.send_json(subscribe_msg)
    
    # Receive subscription confirmation
    response = await ws.receive_json()
    print(f"Subscription response: {response}")
```

#### Subscribe to Specific Event Types
```python
async def subscribe_to_state_changes(ws):
    # Subscribe to state_changed events only
    subscribe_msg = {
        "id": 18,
        "type": "subscribe_events",
        "event_type": "state_changed"
    }
    await ws.send_json(subscribe_msg)
```

#### Subscribe to Triggers
```python
async def subscribe_to_trigger(ws):
    # Subscribe to state trigger
    trigger_msg = {
        "id": 2,
        "type": "subscribe_trigger",
        "trigger": {
            "platform": "state",
            "entity_id": "binary_sensor.motion_occupancy",
            "from": "off",
            "to": "on"
        }
    }
    await ws.send_json(trigger_msg)
```

### Event Handling

#### Process Incoming Events
```python
async def handle_events(ws):
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(msg.data)
            
            if data.get("type") == "event":
                event = data.get("event", {})
                event_type = event.get("event_type")
                event_data = event.get("data", {})
                
                print(f"Event: {event_type}")
                print(f"Data: {event_data}")
                
                # Handle specific event types
                if event_type == "state_changed":
                    handle_state_change(event_data)
                elif event_type == "homeassistant_start":
                    handle_ha_start(event_data)
```

#### State Change Event Example
```json
{
   "id": 18,
   "type": "event",
   "event": {
      "data": {
         "entity_id": "light.bed_light",
         "new_state": {
            "entity_id": "light.bed_light",
            "state": "on",
            "attributes": {
               "brightness": 180,
               "friendly_name": "Bed Light"
            },
            "last_changed": "2016-11-26T01:37:24.265390+00:00",
            "last_updated": "2016-11-26T01:37:24.265390+00:00"
         },
         "old_state": {
            "entity_id": "light.bed_light",
            "state": "off",
            "attributes": {
               "friendly_name": "Bed Light"
            },
            "last_changed": "2016-11-26T01:37:10.466994+00:00",
            "last_updated": "2016-11-26T01:37:10.466994+00:00"
         }
      },
      "event_type": "state_changed",
      "time_fired": "2016-11-26T01:37:24.265429+00:00",
      "origin": "LOCAL"
   }
}
```

### Command Execution

#### Fire Custom Events
```python
async def fire_event(ws, event_type, event_data=None):
    fire_msg = {
        "id": 24,
        "type": "fire_event",
        "event_type": event_type
    }
    
    if event_data:
        fire_msg["event_data"] = event_data
    
    await ws.send_json(fire_msg)
    
    # Wait for response
    response = await ws.receive_json()
    return response
```

#### Ping/Pong for Connection Health
```python
async def ping_ha(ws):
    ping_msg = {
        "id": 19,
        "type": "ping"
    }
    await ws.send_json(ping_msg)
    
    # Wait for pong
    pong_response = await ws.receive_json()
    return pong_response
```

### Unsubscribing

#### Unsubscribe from Events
```python
async def unsubscribe_from_events(ws, subscription_id):
    unsubscribe_msg = {
        "id": 19,
        "type": "unsubscribe_events",
        "subscription": subscription_id
    }
    await ws.send_json(unsubscribe_msg)
    
    response = await ws.receive_json()
    return response
```

### Complete Example

#### Home Assistant Event Listener
```python
import aiohttp
import json
import asyncio

class HomeAssistantClient:
    def __init__(self, url, token):
        self.url = url
        self.token = token
        self.ws = None
        self.subscriptions = {}
    
    async def connect(self):
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.url) as ws:
                self.ws = ws
                
                # Authenticate
                await self._authenticate()
                
                # Subscribe to events
                await self._subscribe_to_events()
                
                # Handle events
                await self._handle_events()
    
    async def _authenticate(self):
        # Receive auth_required
        auth_required = await self.ws.receive_json()
        
        # Send auth
        auth_msg = {
            "type": "auth",
            "access_token": self.token
        }
        await self.ws.send_json(auth_msg)
        
        # Receive auth_ok
        auth_response = await self.ws.receive_json()
        if auth_response.get("type") != "auth_ok":
            raise Exception("Authentication failed")
    
    async def _subscribe_to_events(self):
        subscribe_msg = {
            "id": 1,
            "type": "subscribe_events",
            "event_type": "state_changed"
        }
        await self.ws.send_json(subscribe_msg)
        
        response = await self.ws.receive_json()
        self.subscriptions[1] = response
    
    async def _handle_events(self):
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                
                if data.get("type") == "event":
                    await self._process_event(data["event"])
    
    async def _process_event(self, event):
        event_type = event.get("event_type")
        event_data = event.get("data", {})
        
        print(f"Event: {event_type}")
        print(f"Data: {json.dumps(event_data, indent=2)}")

# Usage
async def main():
    client = HomeAssistantClient(
        "ws://homeassistant.local:8123/api/websocket",
        "YOUR_LONG_LIVED_ACCESS_TOKEN"
    )
    
    try:
        await client.connect()
    except KeyboardInterrupt:
        print("Disconnecting...")

if __name__ == "__main__":
    asyncio.run(main())
```

### Best Practices
- **Long-lived Access Tokens**: Use long-lived access tokens for persistent connections
- **Error Handling**: Implement proper error handling for connection issues
- **Reconnection Logic**: Implement automatic reconnection on connection loss
- **Event Filtering**: Subscribe only to relevant event types to reduce noise
- **Rate Limiting**: Be mindful of Home Assistant's rate limits
- **Connection Health**: Use ping/pong to monitor connection health

---

## TypeScript/React - Frontend Development

### Overview
TypeScript provides static typing for JavaScript, while React is a library for building user interfaces. Together, they provide a robust foundation for frontend development.

### Key Features
- **Static Typing**: Compile-time type checking
- **JSX Support**: Type-safe JSX syntax
- **Component Props**: Strongly typed component interfaces
- **State Management**: Type-safe state handling
- **Error Prevention**: Catch errors at compile time

### Component Development

#### Basic Component with Props
```typescript
import React from 'react';

interface MyProps {
    title: string;
    count: number;
    isActive?: boolean;
}

const MyComponent: React.FC<MyProps> = ({ title, count, isActive = false }) => {
    return (
        <div className={isActive ? 'active' : 'inactive'}>
            <h1>{title}</h1>
            <p>Count: {count}</p>
        </div>
    );
};

export default MyComponent;
```

#### Class Component
```typescript
import React, { Component } from 'react';

interface Props {
    initialCount: number;
}

interface State {
    count: number;
}

class Counter extends Component<Props, State> {
    constructor(props: Props) {
        super(props);
        this.state = {
            count: props.initialCount
        };
    }

    increment = () => {
        this.setState(prevState => ({
            count: prevState.count + 1
        }));
    };

    render() {
        return (
            <div>
                <p>Count: {this.state.count}</p>
                <button onClick={this.increment}>Increment</button>
            </div>
        );
    }
}

export default Counter;
```

#### Component with Children
```typescript
import React from 'react';

interface Props {
    children: React.ReactNode;
    className?: string;
}

const Container: React.FC<Props> = ({ children, className = '' }) => {
    return (
        <div className={`container ${className}`}>
            {children}
        </div>
    );
};

export default Container;
```

#### Component with Event Handlers
```typescript
import React from 'react';

interface Props {
    onSubmit: (data: FormData) => void;
    onCancel: () => void;
}

interface FormData {
    name: string;
    email: string;
}

const ContactForm: React.FC<Props> = ({ onSubmit, onCancel }) => {
    const [formData, setFormData] = React.useState<FormData>({
        name: '',
        email: ''
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(formData);
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="Name"
            />
            <input
                name="email"
                type="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Email"
            />
            <button type="submit">Submit</button>
            <button type="button" onClick={onCancel}>Cancel</button>
        </form>
    );
};

export default ContactForm;
```

### Hooks with TypeScript

#### useState Hook
```typescript
import React, { useState } from 'react';

interface User {
    id: number;
    name: string;
    email: string;
}

const UserProfile: React.FC = () => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    const fetchUser = async (id: number) => {
        setLoading(true);
        try {
            // API call
            const userData = await fetchUserFromAPI(id);
            setUser(userData);
        } catch (error) {
            console.error('Error fetching user:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            {loading && <p>Loading...</p>}
            {user && (
                <div>
                    <h2>{user.name}</h2>
                    <p>{user.email}</p>
                </div>
            )}
        </div>
    );
};
```

#### useEffect Hook
```typescript
import React, { useState, useEffect } from 'react';

interface DataItem {
    id: number;
    value: string;
}

const DataList: React.FC = () => {
    const [data, setData] = useState<DataItem[]>([]);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/api/data');
                const result = await response.json();
                setData(result);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
            }
        };

        fetchData();
    }, []); // Empty dependency array means run once on mount

    if (error) {
        return <div>Error: {error}</div>;
    }

    return (
        <ul>
            {data.map(item => (
                <li key={item.id}>{item.value}</li>
            ))}
        </ul>
    );
};
```

#### Custom Hooks
```typescript
import { useState, useEffect } from 'react';

interface UseApiResult<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
    refetch: () => void;
}

function useApi<T>(url: string): UseApiResult<T> {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await fetch(url);
            const result = await response.json();
            setData(result);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [url]);

    return { data, loading, error, refetch: fetchData };
}

// Usage
const MyComponent: React.FC = () => {
    const { data, loading, error, refetch } = useApi<User[]>('/api/users');

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;

    return (
        <div>
            {data?.map(user => (
                <div key={user.id}>{user.name}</div>
            ))}
            <button onClick={refetch}>Refresh</button>
        </div>
    );
};
```

### Advanced Patterns

#### Generic Components
```typescript
import React from 'react';

interface ListProps<T> {
    items: T[];
    renderItem: (item: T) => React.ReactNode;
    keyExtractor: (item: T) => string | number;
}

function List<T>({ items, renderItem, keyExtractor }: ListProps<T>) {
    return (
        <ul>
            {items.map(item => (
                <li key={keyExtractor(item)}>
                    {renderItem(item)}
                </li>
            ))}
        </ul>
    );
}

// Usage
interface User {
    id: number;
    name: string;
}

const UserList: React.FC = () => {
    const users: User[] = [
        { id: 1, name: 'John' },
        { id: 2, name: 'Jane' }
    ];

    return (
        <List
            items={users}
            keyExtractor={(user) => user.id}
            renderItem={(user) => <span>{user.name}</span>}
        />
    );
};
```

#### Higher-Order Components
```typescript
import React from 'react';

interface WithLoadingProps {
    loading: boolean;
}

function withLoading<P extends object>(
    Component: React.ComponentType<P>
): React.FC<P & WithLoadingProps> {
    return ({ loading, ...props }) => {
        if (loading) {
            return <div>Loading...</div>;
        }
        return <Component {...(props as P)} />;
    };
}

// Usage
interface MyComponentProps {
    title: string;
}

const MyComponent: React.FC<MyComponentProps> = ({ title }) => (
    <h1>{title}</h1>
);

const MyComponentWithLoading = withLoading(MyComponent);
```

#### Context with TypeScript
```typescript
import React, { createContext, useContext, useState } from 'react';

interface Theme {
    primary: string;
    secondary: string;
    background: string;
}

interface ThemeContextType {
    theme: Theme;
    setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [theme, setTheme] = useState<Theme>({
        primary: '#007bff',
        secondary: '#6c757d',
        background: '#ffffff'
    });

    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};

export const useTheme = (): ThemeContextType => {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};
```

### Best Practices
- **Interface Definitions**: Define clear interfaces for all props and state
- **Type Safety**: Use strict TypeScript configuration
- **Component Composition**: Prefer composition over inheritance
- **Error Boundaries**: Implement error boundaries for better error handling
- **Performance**: Use React.memo and useMemo for performance optimization
- **Testing**: Write type-safe tests with proper TypeScript support

---

## Integration Examples

### Home Assistant Event Ingestion Pipeline

```python
import aiohttp
import asyncio
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import json
from datetime import datetime

class HomeAssistantIngestionPipeline:
    def __init__(self, ha_url, ha_token, influx_url, influx_token, influx_org, influx_bucket):
        self.ha_url = ha_url
        self.ha_token = ha_token
        self.influx_url = influx_url
        self.influx_token = influx_token
        self.influx_org = influx_org
        self.influx_bucket = influx_bucket
        
        # Initialize InfluxDB client
        self.influx_client = InfluxDBClient(
            url=influx_url,
            token=influx_token,
            org=influx_org
        )
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
    
    async def start_ingestion(self):
        """Start the Home Assistant event ingestion pipeline"""
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(self.ha_url) as ws:
                # Authenticate with Home Assistant
                await self._authenticate_ha(ws)
                
                # Subscribe to all events
                await self._subscribe_to_events(ws)
                
                # Process events
                await self._process_events(ws)
    
    async def _authenticate_ha(self, ws):
        """Authenticate with Home Assistant WebSocket API"""
        # Receive auth_required
        auth_required = await ws.receive_json()
        print(f"Auth required: {auth_required}")
        
        # Send authentication
        auth_msg = {
            "type": "auth",
            "access_token": self.ha_token
        }
        await ws.send_json(auth_msg)
        
        # Receive auth_ok
        auth_response = await ws.receive_json()
        if auth_response.get("type") != "auth_ok":
            raise Exception("Home Assistant authentication failed")
        print("Home Assistant authentication successful")
    
    async def _subscribe_to_events(self, ws):
        """Subscribe to all Home Assistant events"""
        subscribe_msg = {
            "id": 1,
            "type": "subscribe_events"
        }
        await ws.send_json(subscribe_msg)
        
        response = await ws.receive_json()
        print(f"Event subscription: {response}")
    
    async def _process_events(self, ws):
        """Process incoming Home Assistant events"""
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    
                    if data.get("type") == "event":
                        await self._handle_event(data["event"])
                        
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                except Exception as e:
                    print(f"Error processing event: {e}")
    
    async def _handle_event(self, event):
        """Handle individual Home Assistant events"""
        event_type = event.get("event_type")
        event_data = event.get("data", {})
        time_fired = event.get("time_fired")
        
        # Create InfluxDB point
        point = Point("home_assistant_events") \
            .tag("event_type", event_type) \
            .tag("origin", event.get("origin", "unknown")) \
            .field("event_data", json.dumps(event_data)) \
            .time(time_fired, WritePrecision.NS)
        
        # Add entity-specific tags for state_changed events
        if event_type == "state_changed":
            entity_id = event_data.get("entity_id")
            if entity_id:
                point = point.tag("entity_id", entity_id)
                
                new_state = event_data.get("new_state")
                if new_state:
                    point = point.tag("domain", entity_id.split(".")[0])
                    point = point.field("state", new_state.get("state", ""))
        
        # Write to InfluxDB
        try:
            self.write_api.write(bucket=self.influx_bucket, org=self.influx_org, record=point)
            print(f"Event ingested: {event_type} at {time_fired}")
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")

# Usage
async def main():
    pipeline = HomeAssistantIngestionPipeline(
        ha_url="ws://homeassistant.local:8123/api/websocket",
        ha_token="YOUR_LONG_LIVED_ACCESS_TOKEN",
        influx_url="http://localhost:8086",
        influx_token="YOUR_INFLUXDB_TOKEN",
        influx_org="your-org",
        influx_bucket="home-assistant"
    )
    
    try:
        await pipeline.start_ingestion()
    except KeyboardInterrupt:
        print("Ingestion stopped by user")
    except Exception as e:
        print(f"Pipeline error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

This knowledge base provides comprehensive documentation for all the key technologies used in the Home Assistant Ingestion Layer project, with practical examples and best practices for implementation.
