# Team ID Duplicate Fix - Complete

## Issue Summary

**Problem:** The Sports tab was displaying games from teams the user did not select.

**Root Cause:** Multiple NFL and NHL teams shared the same team ID abbreviations, causing incorrect game matching:
- `dal` = Dallas Cowboys (NFL) AND Dallas Stars (NHL)
- `car` = Carolina Panthers (NFL) AND Carolina Hurricanes (NHL)
- `det` = Detroit Lions (NFL) AND Detroit Red Wings (NHL)
- `buf` = Buffalo Bills (NFL) AND Buffalo Sabres (NHL)
- `phi` = Philadelphia Eagles (NFL) AND Philadelphia Flyers (NHL)
- `pit` = Pittsburgh Steelers (NFL) AND Pittsburgh Penguins (NHL)
- `wsh` = Washington Commanders (NFL) AND Washington Capitals (NHL)
- `ari` = Arizona Cardinals (NFL) AND Arizona Coyotes (NHL)
- `chi` = Chicago Bears (NFL) AND Chicago Blackhawks (NHL)
- `sea` = Seattle Seahawks (NFL) AND Seattle Kraken (NHL)
- `min` = Minnesota Vikings (NFL) AND Minnesota Wild (NHL)

**Impact:** When a user selected "Dallas Cowboys", they would also see Dallas Stars (NHL) games because both used the team ID `dal`.

## Solution

### Backend Changes (`services/sports-data/src/sports_api_client.py`)

1. **Modified `_parse_team()` method** (lines 309-312):
   - Added league prefix to team IDs: `{league.lower()}-{abbreviation.lower()}`
   - Example: `dal` → `nfl-dal` or `nhl-dal`

2. **Updated static team lists**:
   - All NFL teams now use `nfl-` prefix (e.g., `nfl-dal`, `nfl-car`)
   - All NHL teams now use `nhl-` prefix (e.g., `nhl-dal`, `nhl-vgk`)
   - Total: 32 NFL teams + 32 NHL teams = 64 unique team IDs

### Team ID Format

**New Format:** `{league}-{abbreviation}`

**Examples:**
- Dallas Cowboys: `nfl-dal`
- Dallas Stars: `nhl-dal`
- Vegas Golden Knights: `nhl-vgk`
- Carolina Panthers: `nfl-car`
- Carolina Hurricanes: `nhl-car`

## Verification

**Test Query:**
```bash
GET /api/v1/games/upcoming?team_ids=nfl-dal,nhl-vgk&hours=168
```

**Results:**
- ✅ Dallas Cowboys (NFL) game only - no Dallas Stars
- ✅ Vegas Golden Knights (NHL) games only
- ✅ No cross-league contamination

## User Impact

**IMPORTANT:** Users will need to **reselect their teams** because the team IDs have changed.

### User Experience
1. Existing team selections in localStorage use old IDs (`dal`, `vgk`)
2. New team IDs are prefixed (`nfl-dal`, `nhl-vgk`)
3. **Action Required:** Users must go to Settings → Sports Teams and reselect their teams

### Migration Path
- No automatic migration implemented (clean slate approach)
- Users will see "No teams selected" message
- Team selection UI will show teams with new IDs
- Previous selections will not match and will be ignored

## Testing

**Test Scenarios:**
1. ✅ Select Dallas Cowboys → Only NFL Dallas games
2. ✅ Select Dallas Stars → Only NHL Dallas games
3. ✅ Select both → See both leagues correctly filtered
4. ✅ No duplicate games from unselected teams
5. ✅ Vegas Golden Knights games appear correctly

## Files Modified

1. `services/sports-data/src/sports_api_client.py`
   - `_parse_team()` method: Added league prefix to team IDs
   - `_get_nfl_teams()`: Updated all 32 NFL team IDs
   - `_get_nhl_teams()`: Updated all 32 NHL team IDs

## Related Fixes

This fix builds on previous work:
- Multi-day NHL game fetching (for Vegas Golden Knights schedule)
- Property name fixes (snake_case vs camelCase)
- 7-day sliding window for upcoming games

## Date

October 18, 2025

