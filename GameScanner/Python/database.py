import aiosqlite
import os
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
                             title TEXT,
                             description TEXT,
                             thumbnail_url TEXT,
                             likes INTEGER,
                             dislikes INTEGER,
                             visits INTEGER,
                             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
async def insertGameIntoDatabase(universeId: int, title: str, description: str):
    # Inserts game records into the database
    async with aiosqlite.connect(dbFile) as db:
        await db.execute("""
                         INSERT OR REPLACE INTO games (universe_id, title, description, updated_at)
                         VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                         """, (universeId, title, description))
        await db.commit()
