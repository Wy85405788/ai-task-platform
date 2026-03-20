import json

import asyncio

from app.database import async_session, init_db
from app.models import Task


async def migrate():
    await init_db()
    try:
        with open('../tasks_db.json', 'r', encoding='utf-8') as f:
            old_tasks = json.load(f)
    except FileNotFoundError:
        print("❌ 未找到 tasks_db.json，请确认文件路径")
        return

    async with async_session() as session:
        async with session.begin():
            for item in old_tasks:
                # 检查是否已经迁移过（防止重复）
                # 注意：这里我们沿用了你 JSON 里的 id
                new_task = Task(
                    id=item["id"],
                    description=item["description"],
                    status=item["status"],
                    priority=item["priority"],
                    estimated_hours=item.get("estimated_hours", 1),  # 沿用或给默认值
                    tags=item.get("tags", []),
                    user_code=item.get("user_code"),
                    feedback=item.get("feedback"),
                    created_at=item["created_at"]
                )
                session.add(new_task)
        await session.commit()
    print(f"✅ 成功迁移 {len(old_tasks)} 条任务到数据库！")

if __name__ == "__main__":
    asyncio.run(migrate())