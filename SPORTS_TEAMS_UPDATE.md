# Sports Dashboard Teams Update

## Summary

Updated the sports dashboard to include **all 32 NFL teams** and **all 32 NHL teams**, ensuring the following requested teams are available:

✅ **Dallas Cowboys** (NFL - NFC East)
✅ **Las Vegas Raiders** (NFL - AFC West)  
✅ **Vegas Golden Knights** (NHL - Pacific Division)

## Changes Made

### 1. Backend API (`services/sports-data/src/sports_api_client.py`)

Updated `_get_nfl_teams()` method to include all 32 NFL teams:
- **AFC East**: Bills, Dolphins, Patriots, Jets
- **AFC North**: Ravens, Bengals, Browns, Steelers
- **AFC South**: Texans, Colts, Jaguars, Titans
- **AFC West**: Broncos, Chiefs, **Raiders**, Chargers
- **NFC East**: **Cowboys**, Giants, Eagles, Commanders
- **NFC North**: Bears, Lions, Packers, Vikings
- **NFC South**: Falcons, Panthers, Saints, Buccaneers
- **NFC West**: Cardinals, Rams, 49ers, Seahawks

Updated `_get_nhl_teams()` method to include all 32 NHL teams:
- **Atlantic Division**: Bruins, Sabres, Red Wings, Panthers, Canadiens, Senators, Lightning, Maple Leafs
- **Metropolitan Division**: Hurricanes, Blue Jackets, Devils, Islanders, Rangers, Flyers, Penguins, Capitals
- **Central Division**: Coyotes, Blackhawks, Avalanche, Stars, Wild, Predators, Blues, Jets
- **Pacific Division**: Ducks, Flames, Oilers, Kings, Sharks, Kraken, **Golden Knights**, Canucks

### 2. Frontend Fallback Data (`services/health-dashboard/src/components/sports/SetupWizard.tsx`)

Updated `getStaticNFLTeams()` function with complete NFL roster (32 teams)
Updated `getStaticNHLTeams()` function with complete NHL roster (32 teams)

**Purpose**: These fallback functions ensure the team selection wizard works even if the API is unavailable.

## Team Details

### Dallas Cowboys
- **ID**: `dal`
- **Abbreviation**: DAL
- **Division**: NFC East
- **Colors**: Primary #003594 (Blue), Secondary #869397 (Silver)

### Las Vegas Raiders
- **ID**: `lv`
- **Abbreviation**: LV
- **Division**: AFC West
- **Colors**: Primary #000000 (Black), Secondary #A5ACAF (Silver)

### Vegas Golden Knights
- **ID**: `vgk`
- **Abbreviation**: VGK
- **Division**: Pacific
- **Colors**: Primary #B4975A (Gold), Secondary #333F42 (Steel Gray)

## How to Use

1. **Navigate to Sports Tab** in the Health Dashboard (http://localhost:3000)
2. **Run Setup Wizard** (first-time setup) or **Manage Teams** (settings)
3. **Search or scroll** to find your teams:
   - Type "Cowboys" to find Dallas Cowboys
   - Type "Raiders" to find Las Vegas Raiders
   - Type "Golden Knights" or "Vegas" to find Vegas Golden Knights
4. **Select teams** by clicking on the team cards
5. **Confirm selections** to start tracking games

## Testing

The teams can be selected through:
- **Initial Setup Wizard**: 3-step wizard for first-time configuration
- **Team Management**: Settings panel for adding/removing teams
- **Search Function**: Quick search by team name or abbreviation

All teams include:
- Official team colors for visual identification
- Division/conference organization
- Search and filter capabilities
- Team records (when available from API)

## API Usage

The sports dashboard follows an **opt-in model**:
- Only games involving selected teams are fetched
- Free ESPN API tier supports up to 100 daily calls
- Recommended: 3-5 teams per league for optimal performance
- Live games cached for 15 seconds
- Upcoming games cached for 5 minutes

## Notes

- Team data is first fetched from the ESPN API (live data with logos and records)
- If API is unavailable, falls back to static team lists defined in code
- All 32 NFL teams and 32 NHL teams are now available for selection
- Team colors match official branding for better visual experience

