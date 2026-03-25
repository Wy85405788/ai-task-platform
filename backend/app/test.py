from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage
import asyncio
# 1. 像配置数据库连接池一样初始化模型
model = init_chat_model(
    model="qwen3-max-2026-01-23",             # 或者 "qwen-max"
    model_provider="openai",     # 指定供应商
    streaming=True,
    # 如果是国内镜像或自定义端点，在这里传参数
    api_key="sk-d7370b4550e84c6d85c73d63415302d2",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

async def test():
    response = await model.ainvoke([
        SystemMessage(content="你是一个幽默导师"),
        HumanMessage(content="出题！")
    ])
    print(response)



if __name__ == "__main__":
    asyncio.run(test())
    print("Hello, world!")