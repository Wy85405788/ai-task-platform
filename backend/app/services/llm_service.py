# services/ai_task_generator.py

import logging
import os

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from dotenv import load_dotenv

load_dotenv()

class QwenTaskGenerator:
    def __init__(self):
        self.llm = init_chat_model(
            model="qwen3-max-2026-01-23",  # 或者 "qwen-max"
            model_provider="openai",  # 指定供应商
            streaming=True,
            api_key=os.getenv("DASHSCOPE_API_KEY"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个幽默的编程导师。"),
            ("user", "{input_text}")
        ])

        self.chain = self.prompt | self.llm



    # 流式生成任务
    async def stream_generate_task(self, topic: str, on_complete=None):
        """
        核心逻辑：流式生产
        """
        prompt_value = self.prompt.format_prompt(input_text=f"给我布置一个关于 {topic} 的 Python 小挑战")
        async for chunk in self.__deal_with_stream_data(prompt=prompt_value.to_messages(), on_complete=on_complete):
            yield chunk
        # async for chunk in self.llm.astream(
        #     prompt_value.to_messages(),
        #     config={"metadata": {"user_id": "8-year-pro"}},
        #     stream_options={"include_usage": True}
        # ):
        #     if chunk.content:
        #         full_reason += chunk.content
        #         yield f"data: {chunk.content}\n\n"
        #     print(f" 返回的原型：${chunk}")
        #     if chunk.usage_metadata:
        #         token_usage = chunk.usage_metadata.get("total_tokens", 0)
        #         print(f" token使用量： {token_usage}")
        #
        # if on_complete:
        #     await on_complete(full_reason, token_usage)




    # 流式回复用户输入的代码
    async def stream_check_code(self, task_id: int, task_description: str, user_code: str, on_complete=None):
        """
        核心批改逻辑封装在这里
        task_id: 用于定位是哪个任务
        save_callback: 一个回调函数，当流结束时，调用它存入 JSON
        """
        template = ChatPromptTemplate.from_template("""
        你是一个资深的程序猿鼓励师（兼职毒舌代码审查官）。
        用户针对以下任务写了一段代码：

        【任务内容】：
        {task_description}

        【用户代码】：
        {user_code}

        请按以下格式给出评价：
        1. 逻辑评定：简单说明代码是否实现了任务要求。
        2. 优化建议：指出代码中可以改进的地方（性能、可读性）。
        3. 猿式冷笑话：用一种幽默或调侃的方式评价这段代码。

        请使用 Markdown 格式输出。
        """)
        prompt = template.format_messages(
            task_description=task_description,
            user_code=user_code
        )
        try:
            async def check_call_back(full_feedback, token_usage):
                if on_complete:
                    await on_complete(task_id, user_code, full_feedback, token_usage)

            async for chunk in self.__deal_with_stream_data(prompt=prompt, on_complete=check_call_back):
                yield chunk

            # 使用类内部已有的 client
            # token_usage = 0
            # async for chunk in self.llm.astream(
            #     prompt,
            #     config={"metadata": {"user_id": "8-year-pro"}},
            #     stream_options={"include_usage": True}
            # ):
            #     if chunk.content:
            #         full_feedback += chunk.content
            #         yield f"data: {chunk.content}\n\n"
            #
            #     if chunk.usage_metadata:
            #         token_usage = chunk.usage_metadata.get("total_tokens", 0)
            #         print(f" token使用量： {token_usage}")
            #
            # if on_complete:
            #     await on_complete(task_id, user_code, full_feedback, token_usage)


        except Exception as e:
            # 这里的错误处理也可以封装得更统一
            logging.error(f"批改代码时发生错误: {str(e)}")
            yield f"data: ❌ 批改服务出点小差: {str(e)}\n\n"


    async def __deal_with_stream_data(self, prompt, on_complete=None):
        content = ""
        token_usage = 0

        try:
            async for chunk in self.llm.astream(
                prompt,
                config={"metadata": {"user_id": "8-year-pro"}},
                stream_options={"include_usage": True}
            ):
                if chunk.content:
                    content += chunk.content
                    yield f"data: {chunk.content}\n\n"

                if chunk.usage_metadata:
                    token_usage = chunk.usage_metadata.get("total_tokens", 0)
                    print(f" token使用量： {token_usage}")

            if on_complete:
                try:
                    await on_complete(content, token_usage)
                except Exception as e:
                    logging.error(f"Callback 异步保存失败: {str(e)}")

        except Exception as e:
            logging.error(f"流式处理时发生错误: {str(e)}")
            yield f"data: ❌ 服务出点小差: {str(e)}\n\n"