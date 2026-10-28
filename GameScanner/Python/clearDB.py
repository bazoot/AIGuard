import aiosqlite
async def wipeDB():
    async with aiosqlite.connect("roblox_games.db") as db:
        await db.execute("DELETE FROM games;")
        await db.commit()
wipeDB()
print("DB wiped")