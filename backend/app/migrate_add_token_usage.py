import asyncio
from sqlalchemy import text
from app.database import engine

async def migrate():
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(tasks)"))
        columns = [row[1] for row in result.fetchall()]

        if 'token_usage' not in columns:
            await conn.execute(text(
                "ALTER TABLE tasks ADD COLUMN token_usage INTEGER DEFAULT 0"
            ))
            print("✅ token_usage 字段添加成功")
        else:
            print("⚠️ token_usage 字段已存在，跳过")



if __name__ == '__main__':
    asyncio.run(migrate())