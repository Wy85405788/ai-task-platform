from typing import Optional, List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Text, Integer, String, JSON


class Base(DeclarativeBase):
    """所有模型的基类，面试官管这叫 '元数据容器'"""
    pass


class Task(Base):
    __tablename__ = "tasks"

    #主键，自动递增
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # 任务描述，对应 JSON 的 description
    description: Mapped[str] = mapped_column(Text)
    # 状态和优先级，保持你之前的命名
    status: Mapped[str] = mapped_column(String(20), default="待处理")
    priority: Mapped[str] = mapped_column(String(10), default="中")
    # 新增：预计工时 (正如你刚才提到的，我们要把它加进来)
    estimated_hours: Mapped[int] = mapped_column(Integer, default=1)
    # 标签列表：利用 SQLite 的 JSON 支持
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, default=[])
    # 用户代码和反馈，对应你 JSON 里的 user_code 和 feedback
    user_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # 创建时间
    created_at: Mapped[str] = mapped_column(String(20))