# -*- coding: utf-8 -*-
"""
文档解析器 - 支持 PDF、DOC、DOCX、TXT、图片 OCR
"""

import logging
import os
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class DocumentChunk:
    def __init__(self, content: str, source: str, page: Optional[int] = None):
        self.content = content
        self.source = source
        self.page = page

    def __repr__(self) -> str:
        return f"DocumentChunk(source={self.source}, page={self.page}, content_len={len(self.content)})"


class DocumentParser:
    SUPPORTED_EXTENSIONS = {".pdf", ".doc", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".bmp", ".gif"}

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def parse_file(self, file_path: str) -> List[DocumentChunk]:
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"不支持的文件类型: {ext}")
            return []

        if ext == ".pdf":
            return self._parse_pdf(file_path)
        elif ext in {".doc", ".docx"}:
            return self._parse_doc(file_path)
        elif ext == ".txt":
            return self._parse_txt(file_path)
        elif ext in {".png", ".jpg", ".jpeg", ".bmp", ".gif"}:
            return self._parse_image(file_path)
        return []

    def _parse_pdf(self, file_path: str) -> List[DocumentChunk]:
        chunks = []
        try:
            import pypdf

            reader = pypdf.PdfReader(file_path)
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    text = text.strip()
                    if text:
                        chunks.extend(self._chunk_text(text, file_path, page_num))
        except ImportError:
            logger.warning("pypdf 未安装，无法解析 PDF 文件")
        except Exception as e:
            logger.error(f"PDF 解析失败 {file_path}: {e}")
        return chunks

    def _parse_doc(self, file_path: str) -> List[DocumentChunk]:
        chunks = []
        try:
            from docx import Document

            doc = Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text.strip())

            text = "\n".join(full_text)
            if text:
                chunks.extend(self._chunk_text(text, file_path))
        except ImportError:
            logger.warning("python-docx 未安装，无法解析 DOC/DOCX 文件")
        except Exception as e:
            logger.error(f"DOC 解析失败 {file_path}: {e}")
        return chunks

    def _parse_txt(self, file_path: str) -> List[DocumentChunk]:
        chunks = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if text:
                chunks.extend(self._chunk_text(text, file_path))
        except Exception as e:
            logger.error(f"TXT 解析失败 {file_path}: {e}")
        return chunks

    def _parse_image(self, file_path: str) -> List[DocumentChunk]:
        chunks = []
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang="chi_sim+eng")
            if text and text.strip():
                chunks.extend(self._chunk_text(text.strip(), file_path))
        except ImportError:
            logger.warning("pytesseract 或 PIL 未安装，无法解析图片")
        except Exception as e:
            logger.error(f"图片 OCR 解析失败 {file_path}: {e}")
        return chunks

    def _chunk_text(self, text: str, source: str, page: Optional[int] = None) -> List[DocumentChunk]:
        if not text:
            return []

        if len(text) <= self.chunk_size:
            return [DocumentChunk(content=text, source=source, page=page)]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            chunks.append(DocumentChunk(content=chunk_text, source=source, page=page))
            start = end - self.chunk_overlap
        return chunks


def parse_document(file_path: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[DocumentChunk]:
    parser = DocumentParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return parser.parse_file(file_path)