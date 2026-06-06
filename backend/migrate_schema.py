"""One-off schema migration for demo day.
Adds columns introduced in Day 2/3 that may not exist in the Neon DB.
"""
import asyncio
from sqlalchemy import text
from app.core.database import async_session_factory

MIGRATIONS = [
    # Contract additions
    "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS risk_score FLOAT DEFAULT 0.0",

    # Organization additions
    "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS address VARCHAR DEFAULT ''",
    "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS gstin VARCHAR DEFAULT ''",
    "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS cin VARCHAR DEFAULT ''",
    "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS dpo_name VARCHAR DEFAULT ''",
    "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS dpo_email VARCHAR DEFAULT ''",
]

async def main():
    async with async_session_factory() as session:
        for sql in MIGRATIONS:
            try:
                await session.execute(text(sql))
                print(f"OK: {sql}")
            except Exception as e:
                print(f"SKIP (already exists or error): {sql} -- {e}")
        await session.commit()
        print("Migration complete.")

if __name__ == "__main__":
    asyncio.run(main())
