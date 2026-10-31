import aiosqlite
import os
from colours import printC
dbFile = "roblox_games.db"

async def checkDatabaseExists() -> bool:
    #Checks if database file exists
    return os.path.exists(dbFile)

async def createDatabase():
    #Creates tables and indexes in the db
    async with aiosqlite.connect(dbFile) as db:
        await db.execute("""
                         CREATE TABLE IF NOT EXISTS games (
                             universe_id INTEGER PRIMARY KEY,
                             rootPlaceId INTEGER,
                             title TEXT,
                             description TEXT,
                             thumbnail_url TEXT,
                             likes INTEGER,
                             dislikes INTEGER,
                             visits INTEGER,
                             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                             scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                         )
                        """)
        await db.execute("CREATE INDEX IF NOT EXISTS idx_universe_id ON games (universe_id);")
        await db.commit()
        
async def checkIfUniverseExists(universeId: int) -> bool:
    #Checks if a universe ID already exists in the main db
    async with aiosqlite.connect(dbFile) as db:
        async with db.execute("SELECT 1 FROM games WHERE universe_id = ?", (universeId,)) as cursor:
            row = await cursor.fetchone()
            return row is not None
        
async def filterUnplayableGames():
    async with aiosqlite.connect(dbFile) as db:
        query = """
        DELETE FROM GAMES
        WHERE visits < 100
            OR description LIKE '%Roblox Studio!%'
            OR description LIKE '%Roblox%'
        """
        cursor = await db.execute(query)
        await db.commit()
        printC(f"[Database] : Cleaned up {cursor.rowcount} unplayable or low engagement", "brightGreen")  
        
async def insertGameIntoDatabase(universeData: dict):
    # Inserts game records into the database
    async with aiosqlite.connect(dbFile) as db:
        await db.execute("""
                         INSERT OR REPLACE INTO games (
                             universe_id,
                             rootPlaceId,
                             title,
                             description,
                             thumbnail_url,
                             likes,
                             dislikes,
                             visits,
                             updated_at,
                             created_at,
                             scanned_at
                             )
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                         """, (
                             universeData.get("universeId"),
                             universeData.get("rootPlaceId"),
                             universeData.get("title"),
                             universeData.get("description"),
                             universeData.get("thumbnail_url"),
                             universeData.get("likes", 0),
                             universeData.get("dislikes", 0),
                             universeData.get("visits", 0),
                             universeData.get("updated_at"),
                             universeData.get("created_at")
                         ))
        await db.commit()
