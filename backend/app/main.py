# main.py

import os
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from starlette.responses import StreamingResponse
from app.database import init_db, async_session
from app.models import Task
from app.schemas import AITask, CodeCheckRequest
from app.services.llm_service import QwenTaskGenerator
from sqlalchemy import func
print("main.py 已加载")
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware



#region 初始化操作

# 初始化日志
logger = logging.getLogger(__name__)

# 初始化 AI 任务生成器
generator = QwenTaskGenerator()

# 定义生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 【启动时执行】
    print("🚀 正在初始化数据库...")
    await init_db()
    print("✅ 数据库初始化完成！")
    yield
    # 【关闭时执行】
    print("🛑 正在关闭服务...")


# 创建 FastAPI 应用
app = FastAPI(
    title="AI Task Generator",
    description="使用 Qwen3 自动生成每日开发任务",
    version="1.0.0",
    lifespan=lifespan
)

# 获取允许的来源，如果是本地开发就允许所有，如果是生产环境就指定域名
ALLOWED_ORIGINS = [
    "http://localhost:5173",  # 本地 Vite 默认端口
    "http://127.0.0.1:5173",
    "https://ai-task-platform-pi.vercel.app" # 预留你未来的前端线上地址
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_db():
    async with async_session() as session:
        yield session

#endregion

#region 历史数据


async def save_task_result(task_id: int, user_code: str, feedback: str, token_usage: int = 0):
    """
    更新数据库中已存在任务的代码和反馈
    """
    try:
        async with async_session() as db:
            # 1. 找到对应的任务
            result = await db.execute(select(Task).filter(Task.id == task_id))
            task = result.scalar_one_or_none()

            if task:
                # 2. 更新字段
                task.user_code = user_code
                task.feedback = feedback
                task.status = "已完成"  # 既然有了反馈，通常意味着任务完成了
                task.token_usage += token_usage
                # 3. 提交更改
                await db.commit()
                logger.info(f"✅ 任务 {task_id} 的代码和反馈已更新到数据库。")
            else:
                logger.warning(f"⚠️ 未找到 ID 为 {task_id} 的任务，无法更新。")
    except Exception as e:
        logger.error(f"❌ 更新任务结果失败: {e}")


#endregion

# region 路由
@app.get("/task/history")
async def get_task_history(db: AsyncSession = Depends(get_db)):
    # SQL: SELECT * FROM tasks ORDER BY id DESC
    result = await db.execute(select(Task).order_by(Task.id.desc()))
    tasks = result.scalars().all()
    return tasks


@app.get("/task/stream")
async def get_stream(task_id: int, topic: str = "Python 基础"):
    # 这里的参数名和逻辑完全遵循你源码中的定义
    # 定义完成时的回调：更新那条已经存在的记录
    async def update_task_content(full_task_json_str: str, token_usage: int = 0):
        async with async_session() as db:
            result = await db.execute(select(Task).filter(Task.id == task_id))
            task_record = result.scalar_one_or_none()
            if task_record:
                task_record.description = full_task_json_str.strip()
                task_record.status = "进行中"  # 生成完了，状态改为进行中
                task_record.token_usage += token_usage
                await db.commit()
                logger.info(f"✅ 任务 {task_id} 的内容已同步至数据库")
    # 保持你原有的 StreamingResponse 调用方式
    return StreamingResponse(
        generator.stream_generate_task(topic=topic, on_complete=update_task_content),
        media_type="text/event-stream"
    )

@app.post("/task/check")
async def check_task_code(request: CodeCheckRequest):
    """
    路由只负责接收参数，并调用 service 层提供的功能
    """
    return StreamingResponse(
        generator.stream_check_code(
            task_id=request.task_id,
            task_description=request.task_description,
            user_code=request.user_code,
            on_complete=save_task_result
        ),
        media_type="text/event-stream"
    )

# 新增：预创建任务接口
@app.post("/task/create")
async def create_task_placeholder(db: AsyncSession = Depends(get_db)):
    try:
        # 1. 立即创建一个占位任务
        new_task = Task(
            description="",  # 暂时为空
            status="生成中",
            priority="中",
            estimated_hours=1,
            tags=["Python", "每日挑战"],
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_code=None,
            feedback=None
        )
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)  # 拿到真正的数据库自增 ID
        logger.info(f"✅ 已预创建数据库记录，ID: {new_task.id}")
        return {"id": new_task.id}
    except Exception as e:
        logger.error(f"❌ 预创建任务失败: {e}")
        raise HTTPException(status_code=500, detail="创建任务失败")

#endregion

