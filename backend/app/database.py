import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.models import Base


# 1. 获取当前文件 (database.py) 的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 获取 backend 文件夹的路径 (即 app 的上一层)
# os.path.join 会自动处理 Windows 和 Linux 的斜杠差异（/ vs \）
backend_dir = os.path.dirname(current_dir)


# 2. 核心修正：把 backend_dir 传进去作为默认值
# 这样：有环境变量用环境变量（云端），没有就用 backend/tasks.db（本地）
db_path = os.environ.get("DB_PATH", os.path.join(backend_dir, "tasks.db"))
# 💡 关键一步：确保数据库所在的目录存在
db_dir = os.path.dirname(db_path)
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)


# 3. 构造数据库连接字符串
# 注意：SQLite 的绝对路径在 Windows 下通常需要四个斜杠 sqlite+aiosqlite:////D:/...
DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

# 2. 创建异步引擎 (Engine)
# echo=True 会在控制台打印生成的 SQL 语句，开发阶段非常有帮助
engine = create_async_engine(DATABASE_URL, echo=True)

# 3. 创建异步会话工厂 (Session Factory)
# expire_on_commit=False 是为了防止提交后对象属性失效，这在异步环境下非常重要
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
# 4. 初始化数据库函数
async def init_db():
    async with engine.begin() as conn:
        # 这一行会扫描 models.py 里的所有类，并在数据库里建表
        await conn.run_sync(Base.metadata.create_all)
