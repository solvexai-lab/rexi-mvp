"""Backfill risk_score from RiskAssessment for existing contracts."""
import asyncio
from sqlalchemy import text
from app.core.database import async_session_factory

async def main():
    async with async_session_factory() as session:
        await session.execute(text("""
            UPDATE contracts
            SET risk_score = (
                SELECT overall_score
                FROM risk_assessments
                WHERE risk_assessments.contract_id = contracts.id
                ORDER BY created_at DESC
                LIMIT 1
            )
            WHERE risk_score = 0.0
        """))
        await session.commit()
        print("Risk scores updated.")

if __name__ == "__main__":
    asyncio.run(main())
