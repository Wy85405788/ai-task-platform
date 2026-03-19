# schemas.py
from typing import Literal, Optional

from pydantic import BaseModel

class AITask(BaseModel):
    id: int
    description: str
    status: str
    priority: Literal["高", "中", "低"]  # 实际可加 Literal["高", "中", "低"]
    estimated_hours: int
    tags: list[str]
    created_at: str
    # 新增下面两个字段，设为 Optional 以后，初始生成任务时它们可以是 None
    user_code: Optional[str] = None  #存放用户提交的代码
    feedback: Optional[str] = None   #存放AI对代码的回复


class CodeCheckRequest(BaseModel):
    task_id: int
    task_description: str
    user_code: str