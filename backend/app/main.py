# main.py

import os

from starlette.responses import StreamingResponse

from app.schemas import AITask, CodeCheckRequest
from app.services.llm_service import QwenTaskGenerator

print("main.py 已加载")
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
import json
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List



#region 初始化操作

# 初始化日志
logger = logging.getLogger(__name__)

# 初始化 AI 任务生成器
generator = QwenTaskGenerator()

# 创建 FastAPI 应用
app = FastAPI(
    title="AI Task Generator",
    description="使用 Qwen3 自动生成每日开发任务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#endregion

#region 历史数据

#定义历史数据存储位置
TASKS_FILE = "tasks_db.json"

#启动时加载历史数据
def load_history():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


async def save_task_result(task_id: int, user_code: str, feedback: str):
    """
    这是传给 service 的回调函数
    """
    # 1.读取现有文件
    tasks = []
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            tasks = json.load(f)

    # 2.找到对应的任务并更新
    for t in tasks:
        if t["id"] == task_id:
            t["user_code"] = user_code
            t["feedback"] = feedback
            break
    # 3.写回文件
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)
    logger.info(f"任务 {task_id} 记录已持久化。")


#endregion

# region 路由
@app.get("/task/today", response_model=AITask)
async def get_today_task():
    try:
        # 现在 generate_task() 返回 dict
        task_dict = await generator.generate_task()
        # 动态设置 created_at
        import time
        task_dict["id"] = int(time.time())
        task_dict["created_at"] = datetime.now().strftime("%Y-%m-%d")
        tasks = load_history()
        tasks.insert(0, task_dict)
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks[:20], f, ensure_ascii=False, indent=2)

        return AITask(**task_dict)
    except Exception as e:
        logger.error(f"生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/history", response_model=List[AITask])
async def get_task_history():
    """
    直接从 JSON 文件读取并返回
    """
    try:
        # 直接调用你上面定义好的加载函数
        tasks_data = load_history()
        # 转换成 Pydantic 模型列表（只取最近 10 条）
        return [AITask(**task) for task in tasks_data[:10]]
    except Exception as e:
        logger.error(f"获取历史任务失败: {str(e)}")
        return []

@app.get("/task/stream")
async def get_stream():
    async def save_new_task(full_task_json_str: str):
        try:
            # 2. 补全后端数据：ID 和 时间
            new_task_dict = {
                "id": int(time.time()),
                "description": full_task_json_str.strip(),  # 直接使用传入的参数
                "status": "待处理",
                "priority": "中",
                "estimated_hours": 1,
                "tags": ["Python", "每日挑战"],
                "created_at": datetime.now().strftime("%Y-%m-%d"),
                "user_code": None,
                "feedback": None
            }

            # 3. 读取并更新文件
            tasks = load_history()
            tasks.insert(0, new_task_dict)
            with open(TASKS_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks[:20], f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 流式生成的任务 {new_task_dict['id']} 已成功落盘")
        except Exception as e:
            logger.error(f"❌ 自动保存流式任务失败: {e}")

    return StreamingResponse(
        generator.stream_generate_task(on_complete=save_new_task),
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


#endregion