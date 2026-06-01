from pathlib import Path
from typing import Dict, Any
from .base import BaseConverter

class ImageConverter(BaseConverter):
    SUPPORTED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
    
    def __init__(self):
        self._ocr = None
    
    def _get_ocr(self):
        if self._ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self._ocr = RapidOCR()
        return self._ocr
    
    async def convert_to_markdown(self, file_path: Path, lang: str = None) -> Dict[str, Any]:
        """
        图片转Markdown (使用 RapidOCR 识别文字，无需安装 Tesseract)
        """
        try:
            ocr = self._get_ocr()
            result, elapse = ocr(str(file_path))
            
            # 提取识别文字
            texts = []
            if result:
                for item in result:
                    texts.append(item[1])
            
            # 获取图片信息
            from PIL import Image
            img = Image.open(str(file_path))
            width, height = img.size
            
            # 生成Markdown
            md_content = []
            md_content.append(f"![图片]({file_path.name})")
            md_content.append("")
            
            if texts:
                md_content.append("## 识别文字")
                md_content.append("")
                md_content.append("\n".join(texts))
            else:
                md_content.append("（未识别到文字）")
            
            return {
                "success": True,
                "content": "\n".join(md_content),
                "image_size": f"{width}x{height}",
                "text_length": sum(len(t) for t in texts)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def convert_from_markdown(self, md_content: str, output_path: Path) -> Path:
        """Markdown转图片（需要额外工具支持）"""
        raise NotImplementedError("Markdown转图片功能需要额外配置")
