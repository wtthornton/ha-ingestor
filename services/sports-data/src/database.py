"""
Database service for team persistence using aiosqlite
Story 11.5: Team Persistence Implementation
"""

import aiosqlite
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class TeamDatabase:
    """Async SQLite database for team persistence"""
    
    def __init__(self, db_path: str = "data/sports_teams.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def init_db(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_teams (
                    user_id TEXT PRIMARY KEY,
                    nfl_teams TEXT,  -- JSON array as string
                    nhl_teams TEXT,  -- JSON array as string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS update_user_teams_timestamp 
                AFTER UPDATE ON user_teams
                BEGIN
                    UPDATE user_teams SET updated_at = CURRENT_TIMESTAMP WHERE user_id = NEW.user_id;
                END
            """)
            
            await db.commit()
            logger.info("Database initialized successfully")
    
    async def save_user_teams(self, user_id: str, nfl_teams: List[str], nhl_teams: List[str]) -> bool:
        """Save user's selected teams to database"""
        import json
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Convert lists to JSON strings
                nfl_json = json.dumps(nfl_teams)
                nhl_json = json.dumps(nhl_teams)
                
                await db.execute("""
                    INSERT OR REPLACE INTO user_teams (user_id, nfl_teams, nhl_teams)
                    VALUES (?, ?, ?)
                """, (user_id, nfl_json, nhl_json))
                
                await db.commit()
                logger.info(f"Saved teams for user {user_id}: NFL={nfl_teams}, NHL={nhl_teams}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving teams for user {user_id}: {e}")
            return False
    
    async def get_user_teams(self, user_id: str) -> Optional[Dict[str, List[str]]]:
        """Get user's selected teams from database"""
        import json
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT nfl_teams, nhl_teams FROM user_teams WHERE user_id = ?
                """, (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    
                    if row:
                        nfl_teams = json.loads(row[0]) if row[0] else []
                        nhl_teams = json.loads(row[1]) if row[1] else []
                        
                        logger.info(f"Retrieved teams for user {user_id}: NFL={nfl_teams}, NHL={nhl_teams}")
                        return {
                            "nfl_teams": nfl_teams,
                            "nhl_teams": nhl_teams
                        }
                    else:
                        logger.info(f"No teams found for user {user_id}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error retrieving teams for user {user_id}: {e}")
            return None
    
    async def get_all_user_teams(self) -> Dict[str, Dict[str, List[str]]]:
        """Get all users' team selections (for event detector)"""
        import json
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT user_id, nfl_teams, nhl_teams FROM user_teams
                """) as cursor:
                    users = {}
                    async for row in cursor:
                        user_id = row[0]
                        nfl_teams = json.loads(row[1]) if row[1] else []
                        nhl_teams = json.loads(row[2]) if row[2] else []
                        
                        users[user_id] = {
                            "nfl_teams": nfl_teams,
                            "nhl_teams": nhl_teams
                        }
                    
                    logger.info(f"Retrieved teams for {len(users)} users")
                    return users
                    
        except Exception as e:
            logger.error(f"Error retrieving all user teams: {e}")
            return {}
    
    async def delete_user_teams(self, user_id: str) -> bool:
        """Delete user's team selections"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM user_teams WHERE user_id = ?", (user_id,))
                await db.commit()
                logger.info(f"Deleted teams for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting teams for user {user_id}: {e}")
            return False

# Global database instance
team_db = TeamDatabase()
