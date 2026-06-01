from abc import ABC, abstractmethod
from typing import Dict, Any
from pathlib import Path

class BaseConverter(ABC):
    """文档转换器基类"""
    
    SUPPORTED_EXTENSIONS = []
    
    @abstractmethod
    async def convert_to_markdown(self, file_path: Path) -> Dict[str, Any]:
        """转换文档为Markdown"""
        pass
    
    @abstractmethod
    async def convert_from_markdown(self, md_content: str, output_path: Path) -> Path:
        """将Markdown转换为其他格式"""
        pass
    
    def get_supported_extensions(self):
        """获取支持的文件扩展名"""
        return self.SUPPORTED_EXTENSIONS
    
    def validate_file(self, file_path: Path) -> bool:
        """验证文件格式"""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS