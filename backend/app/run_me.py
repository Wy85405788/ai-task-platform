from app.services.pdf_processor import PDFProcessor, TencentReportSplitter
from app.services.vector_service import VectorService


def main():
    path = './2026031800389_c.pdf'

    processor = PDFProcessor(path)
    result = processor.extract_text()

    splitter = TencentReportSplitter()
    chunks = splitter.split(result)

    print(f"📊 原始总字数: {len(result)}")
    print(f"📦 切分后的碎片总数: {len(chunks)}")

    # print("\n--- 随机检查第 5 个碎片的内容 ---")
    # print(chunks[4])  # 看看是不是一段完整的业务描述
    # print("--------------------------------")
    svc = VectorService()
    svc.save_chunks(chunks)

    retriever = svc.get_retriever(k=2)

    query = "腾讯在AI大模型方面的投入如何"
    docs = retriever.invoke(query)
    print(f"🔍 搜到了 {len(docs)} 个相关片段：")
    for doc in docs:
        print(f"--- 片段内容 ---\n{doc.page_content[:200]}...\n")



if __name__ == "__main__":
    main()
