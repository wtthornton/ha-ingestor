# Calendar Service

Google Calendar integration for occupancy prediction and smart home preparation.

## Purpose

Enable predictive automation by analyzing calendar events - prepare home before arrival, enable eco mode when away all day, optimize based on work-from-home schedules.

## Features

- Fetches calendar events every 15 minutes
- Predicts home occupancy based on event locations
- Detects work-from-home days
- Calculates estimated arrival times
- OAuth2 automatic token refresh
- Stores predictions in InfluxDB

## Environment Variables

Required:
- `GOOGLE_CLIENT_ID` - OAuth client ID
- `GOOGLE_CLIENT_SECRET` - OAuth client secret
- `GOOGLE_REFRESH_TOKEN` - OAuth refresh token
- `INFLUXDB_TOKEN` - InfluxDB token

## OAuth Setup

### 1. Create Google Cloud Project

1. Go to https://console.cloud.google.com
2. Create new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download credentials JSON

### 2. Get Refresh Token

```python
# Run this script once to get refresh token
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

print(f"GOOGLE_CLIENT_ID={creds.client_id}")
print(f"GOOGLE_CLIENT_SECRET={creds.client_secret}")
print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
```

### 3. Add to .env

```bash
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REFRESH_TOKEN=your_refresh_token
```

## InfluxDB Schema

```
Measurement: occupancy_prediction
Tags:
  source: "calendar"
  user: "primary"
Fields:
  currently_home: boolean
  wfh_today: boolean
  confidence: float (0-1)
  hours_until_arrival: float
```

## Automation Examples

```yaml
automation:
  - alias: "Prepare Home Before Arrival"
    trigger:
      - platform: template
        value_template: >
          {{ state_attr('sensor.occupancy_prediction', 'hours_until_arrival') | float < 0.5 }}
    condition:
      - condition: state
        entity_id: sensor.occupancy_prediction
        attribute: currently_home
        state: false
    action:
      - service: climate.set_temperature
        data:
          entity_id: climate.living_room
          temperature: 72
      - service: light.turn_on
        entity_id: light.entry
```

## License

MIT License

