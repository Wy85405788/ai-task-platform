from sqlalchemy import func
from sqlalchemy.future import select

from app.database import async_session
from app.models import Task


# region 数据库查询工具

#  获取使用的token总量
async def get_total_token_usage() -> int:
    async with async_session() as db:
        result = await db.execute(
            select(func.sum(Task.token_usage))
        )
        total = result.scalar()
        return total if total else 0
# endregion