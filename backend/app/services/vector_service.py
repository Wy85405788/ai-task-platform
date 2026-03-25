import os

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

class VectorService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model='text-embedding-v4',
            api_key="sk-d7370b4550e84c6d85c73d63415302d2",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.persist_directory = "./chroma_db"

    def save_chunks(self, chunks: list[str]):
        """
        将碎片向量化并持久化到本地
        """
        # 1. 过滤掉可能存在的空字符串或非字符串（防御性编程）
        print(f"📦 正在将 {len(chunks)} 个碎片写入向量数据库...")
        vector_db = Chroma.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
            collection_name="tencent_annual_report"  # 给你的数据集起个名
        )
        print(f"✅ 向量数据库已就绪，存储路径: {self.persist_directory}")
        return vector_db

    def get_retriever(self, k=3):
        """
        这是 1.3 版本最推荐的用法：直接返回一个检索器 (Retriever)
        """
        db = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="tencent_annual_report"
        )
        # 将数据库转变为一个“搜索引擎”接口
        return db.as_retriever(search_kwargs={"k": k})
