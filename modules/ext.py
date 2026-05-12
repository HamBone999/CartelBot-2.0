import aiosqlite

async def execute(db, query, *values):
    """Helper used by bank and inventory"""
    async with aiosqlite.connect(db.filename) as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(query, values)
            await conn.commit()
            if query.strip().upper().startswith("SELECT"):
                return await cursor.fetchall()
    return None
