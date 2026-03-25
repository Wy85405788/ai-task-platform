import fitz
import re

from langchain_text_splitters import RecursiveCharacterTextSplitter


class PDFProcessor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_text(self) -> str:
        """
        从 PDF 中提取纯文本，并进行基础清洗
        """
        doc = fitz.open(self.file_path)
        full_text = ""

        for page_num, page in enumerate(doc):
            text = page.get_text()
            # 提取每一页的文本
            text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
            text = re.sub(r'(?<=[^\n])\n(?=[^\n])', ' ', text)

            full_text += f"\n\n--- 第 {page_num + 1} 页 ---\n\n" + text

        doc.close()
        return full_text


class TencentReportSplitter:
    def __init__(self):
        # chunk_size: 每个杯子装多少水（建议 800-1000 字符，适合财报）
        # chunk_overlap: 杯子之间重叠多少，防止一句话被切断（建议 10%-15%）
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["--- 第", "\n\n", "\n", "。", "！", "？", " ", ""]
        )

    def split(self, text: str):
        return self.splitter.split_text(text)