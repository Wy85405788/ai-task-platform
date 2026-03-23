# services/ai_task_generator.py

import logging
import json
import os

import logger
from openai import AsyncOpenAI, APIStatusError, APIConnectionError, RateLimitError
from dotenv import load_dotenv

load_dotenv()

class QwenTaskGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY"),
        )
        self.model = "qwen3-max-2026-01-23"
    #流式生成任务
    async def stream_generate_task(self, on_complete=None):
        """
        核心逻辑：流式生产
        """
        full_response = ""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个幽默的编程导师。"},
                {"role": "user", "content": "给我布置一个今天的 Python 小挑战。"}
            ],
            stream=True,  # 🔥 开启流式传输
            stream_options={ "include_usage": True}
        )
        # 这里用 async for 不用while是为了让cpu不被一直占用，这是处理并发的关键
        async for chunk in response:
            # 提取碎片内容
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                # SSE 协议要求以 data: 开头，以 \n\n 结尾
                yield f"data: {content}\n\n"
            if chunk.usage:
                print(f"输入 Tokens: {chunk.usage.prompt_tokens}")
                print(f"输出 Tokens: {chunk.usage.completion_tokens}")
                print(f"总计 Tokens: {chunk.usage.total_tokens}")


        # 流结束，触发保存
        if on_complete:
            await on_complete(full_response)




    #流式回复用户输入的代码
    async def stream_check_code(self, task_id: int, task_description: str, user_code: str, on_complete=None):
        """
        核心批改逻辑封装在这里
        task_id: 用于定位是哪个任务
        save_callback: 一个回调函数，当流结束时，调用它存入 JSON
        """
        full_feedback = ""
        check_prompt = f"""
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
        """

        try:
            # 使用类内部已有的 client
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": check_prompt}],
                stream=True
            )

            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    full_feedback += content
                    yield f"data: {content}\n\n"

            if on_complete:
                await on_complete(task_id, user_code, full_feedback)

        except Exception as e:
            # 这里的错误处理也可以封装得更统一
            logging.error(f"批改代码时发生错误: {str(e)}")
            yield f"data: ❌ 批改服务出点小差: {str(e)}\n\n"


    #直接生成任务
    async def generate_task(self) -> dict:
        """
        调用 Qwen 模型生成结构化任务（直接返回 JSON 字典）
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一个专业的开发任务生成器。请严格按照以下 JSON 格式输出，"
                    "不要包含任何额外文本、解释或 markdown：\n"
                    "{\n"
                    '  "description": "任务描述",\n'
                    '  "priority": "高",\n'
                    '  "estimated_hours": 3\n'
                    "}\n"
                    "要求：\n"
                    "- description: 清晰、可执行的编程任务，包含技术关键词\n"
                    '- priority: 必须是 "高"、"中" 或 "低"\n'
                    "- estimated_hours: 整数，范围 1~8"
                )
            },
            {
                "role": "user",
                "content": "请生成一个今日开发任务。"
            }
        ]

        try:
            logger.info("Sending request to Qwen for structured task...")

            completion = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                timeout=30.0
            )
            raw_content = completion.choices[0].message.content.strip()
            logger.info(f"Raw AI response: {raw_content[:100]}...")

            # 尝试提取 JSON（兼容 AI 偶尔加 ```json ... ```）
            if raw_content.startswith("```json"):
                raw_content = raw_content[7:]  # 去掉 ```json
            if raw_content.endswith("```"):
                raw_content = raw_content.rstrip("`")

            # 解析 JSON
            task_data = json.loads(raw_content)

            # 验证必要字段
            required_keys = {"description", "priority", "estimated_hours"}
            if not required_keys.issubset(task_data.keys()):
                raise ValueError(f"缺少必要字段，实际返回: {task_data.keys()}")

            # 补全固定字段（前端仍需要）
            task_data.update({
                "id": 1,  # 暂时固定，历史功能再改
                "status": "待完成",
                "tags": ["ai-generated"],
                "created_at": "2026-03-19"  # 实际用 datetime.now().strftime("%Y-%m-%d")
            })

            logger.info("AI task parsed successfully.")
            return task_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e} | Raw: {raw_content}")
            raise Exception("AI 返回格式错误，请重试")

        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise Exception("API 调用频率超限，请稍后再试")

        except APIStatusError as e:
            logger.error(f"DashScope API error: {e.status_code} - {e.response.text}")
            raise Exception(f"AI 服务异常: {e.status_code}")

        except APIConnectionError as e:
            logger.error(f"Connection failed: {e}")
            raise Exception("网络连接失败，请检查网络")

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise Exception("AI 生成失败，请稍后重试")
