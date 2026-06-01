from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from markitdown import MarkItDown
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import tempfile
import shutil
import uuid
import json
import zipfile
import io

# 导入转换器
from converters import (
    PDFConverter,
    DocxConverter,
    ExcelConverter,
    PPTConverter,
    ImageConverter
)

# ========== 初始化应用 ==========
app = FastAPI(
    title="MarkFlow",
    description="Multi-format Document Converter — PDF, Word, Excel, PPT, Images ↔ Markdown",
    version="2.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建目录
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ========== 转换器注册 ==========
converters = {
    '.pdf': PDFConverter(),
    '.docx': DocxConverter(),
    '.xlsx': ExcelConverter(),
    '.xls': ExcelConverter(),
    '.pptx': PPTConverter(),
    '.jpg': ImageConverter(),
    '.jpeg': ImageConverter(),
    '.png': ImageConverter(),
    '.bmp': ImageConverter(),
    '.tiff': ImageConverter(),
    '.gif': ImageConverter(),
}

# 支持的转换格式
SUPPORTED_CONVERSIONS = {
    "to_markdown": [".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"],
    "from_markdown": [".docx", ".xlsx", ".pptx", ".pdf"]
}

# ========== 前端页面 ==========
@app.get("/", response_class=HTMLResponse)
async def home():
    # 读取外部HTML文件
    html_path = Path(__file__).parent / "templates" / "index.html"
    return html_path.read_text(encoding="utf-8")

# ========== 工具函数 ==========
def get_converter(file_ext: str):
    """获取对应的转换器"""
    return converters.get(file_ext.lower())

def save_upload_file(file: UploadFile, file_id: str) -> Path:
    """保存上传的文件"""
    file_path = UPLOAD_DIR / f"{file_id}{Path(file.filename).suffix}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return file_path

def cleanup_file(file_path: Path):
    """清理临时文件"""
    try:
        if file_path.exists():
            file_path.unlink()
    except:
        pass

# ========== API 路由 ==========

# 1. 文档转 Markdown
@app.post("/convert/to-markdown")
async def convert_to_markdown(file: UploadFile = File(...)):
    """
    将文档转换为 Markdown 格式
    支持: PDF, DOCX, XLSX, PPTX, 图片
    """
    import time
    start_time = time.time()
    
    # 验证文件类型
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in SUPPORTED_CONVERSIONS["to_markdown"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，支持: {', '.join(SUPPORTED_CONVERSIONS['to_markdown'])}"
        )
    
    # 保存上传文件
    file_id = str(uuid.uuid4())[:8]
    file_path = save_upload_file(file, file_id)
    
    try:
        # 获取转换器
        converter = get_converter(file_ext)
        if not converter:
            raise HTTPException(status_code=400, detail=f"未找到 {file_ext} 格式的转换器")
        
        # 执行转换
        result = await converter.convert_to_markdown(file_path)
        
        if not result["success"]:
            return {"success": False, "error": result["error"]}
        
        markdown_content = result["content"]
        
        # 保存结果文件
        output_name = file.filename.rsplit('.', 1)[0] + '.md'
        output_path = OUTPUT_DIR / output_name
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        processing_time = round(time.time() - start_time, 2)
        
        return {
            "success": True,
            "filename": file.filename,
            "markdown": markdown_content,
            "char_count": len(markdown_content),
            "processing_time": processing_time,
            "output_file": output_name,
            "metadata": {k: v for k, v in result.items() if k not in ["success", "content"]}
        }
    
    except HTTPException as e:
        return {"success": False, "error": str(e.detail) if hasattr(e, 'detail') else str(e)}
    except Exception as e:
        return {"success": False, "error": f"转换失败: {str(e)}"}
    finally:
        cleanup_file(file_path)


# 2. Markdown 转文档
@app.post("/convert/from-markdown")
async def convert_from_markdown(
    markdown: str = Form(...),
    format: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """
    将 Markdown 转换为其他文档格式
    支持: DOCX, XLSX, PPTX, PDF
    """
    import time
    start_time = time.time()
    
    # 验证目标格式

    if not format.startswith('.'):
        format = '.' + format
    if format not in SUPPORTED_CONVERSIONS["from_markdown"]:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的目标格式: {format}，支持: {', '.join(SUPPORTED_CONVERSIONS['from_markdown'])}"
        )
    
    # 如果上传了md文件，优先使用文件内容
    if file:
        content = await file.read()
        markdown_content = content.decode('utf-8')
    else:
        markdown_content = markdown
    
    if not markdown_content.strip():
        raise HTTPException(status_code=400, detail="Markdown内容不能为空")
    
    try:
        # 生成输出文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"converted_{timestamp}{format}"
        output_path = OUTPUT_DIR / output_filename
        
        # 根据格式选择转换器
        converter = None
        if format == ".docx":
            converter = DocxConverter()
        elif format in [".xlsx", ".xls"]:
            converter = ExcelConverter()
        elif format == ".pptx":
            converter = PPTConverter()
        elif format == ".pdf":
            # PDF转换需要特殊处理，这里简化为使用MarkItDown的逆向功能
            # 实际可能需要使用weasyprint或pandoc
            raise HTTPException(
                status_code=501, 
                detail="Markdown转PDF功能暂未实现，请选择其他格式"
            )
        
        if not converter:
            raise HTTPException(status_code=500, detail="未找到合适的转换器")
        
        # 执行转换
        result_path = await converter.convert_from_markdown(markdown_content, output_path)
        
        if not result_path.exists():
            raise HTTPException(status_code=500, detail="转换失败，未生成输出文件")
        
        processing_time = round(time.time() - start_time, 2)
        
        # 返回文件流
        return FileResponse(
            path=str(result_path),
            filename=output_filename,
            media_type="application/octet-stream",
            headers={
                "X-Processing-Time": str(processing_time),
                "X-Char-Count": str(len(markdown_content))
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


# 3. 批量转换
@app.post("/convert/batch")
async def convert_batch(
    files: List[UploadFile] = File(...),
    output_format: str = Form("markdown")
):
    """
    批量转换多个文件
    支持同时上传多个文件，统一转换为指定格式
    """
    import time
    start_time = time.time()
    
    if not files:
        raise HTTPException(status_code=400, detail="请上传至少一个文件")
    
    results = []
    success_count = 0
    fail_count = 0
    
    # 创建临时目录
    batch_id = str(uuid.uuid4())[:8]
    batch_dir = OUTPUT_DIR / f"batch_{batch_id}"
    batch_dir.mkdir(exist_ok=True)
    
    for file in files:
        file_result = {
            "filename": file.filename,
            "status": "pending",
            "output": None,
            "error": None
        }

        
        try:
            # 验证文件类型
            file_ext = Path(file.filename).suffix.lower()
            
            if output_format == "markdown":
                # 转换为Markdown
                if file_ext not in SUPPORTED_CONVERSIONS["to_markdown"]:
                    file_result["status"] = "failed"
                    file_result["error"] = f"不支持的格式: {file_ext}"
                    fail_count += 1
                    results.append(file_result)
                    continue
                
                # 保存文件
                file_path = save_upload_file(file, str(uuid.uuid4())[:8])
                
                # 获取转换器
                converter = get_converter(file_ext)
                if not converter:
                    file_result["status"] = "failed"
                    file_result["error"] = f"未找到 {file_ext} 转换器"
                    fail_count += 1
                    results.append(file_result)
                    cleanup_file(file_path)
                    continue
                
                # 转换
                result = await converter.convert_to_markdown(file_path)
                cleanup_file(file_path)
                
                if not result["success"]:
                    file_result["status"] = "failed"
                    file_result["error"] = result["error"]
                    fail_count += 1
                else:
                    # 保存Markdown文件
                    md_filename = file.filename.rsplit('.', 1)[0] + '.md'
                    md_path = batch_dir / md_filename
                    with open(md_path, 'w', encoding='utf-8') as f:
                        f.write(result["content"])
                    
                    file_result["status"] = "success"
                    file_result["output"] = md_filename
                    file_result["char_count"] = len(result["content"])
                    success_count += 1
            else:
                # Markdown 转其他格式
                if file_ext not in ['.md', '.markdown', '.txt']:
                    # 不是 markdown 文件，先转 markdown 再转目标格式
                    if file_ext not in SUPPORTED_CONVERSIONS["to_markdown"]:
                        file_result["status"] = "failed"
                        file_result["error"] = f"不支持的格式: {file_ext}"
                        fail_count += 1
                        results.append(file_result)
                        continue

                    file_path = save_upload_file(file, str(uuid.uuid4())[:8])
                    converter = get_converter(file_ext)
                    if not converter:
                        file_result["status"] = "failed"
                        file_result["error"] = f"未找到 {file_ext} 转换器"
                        fail_count += 1
                        results.append(file_result)
                        cleanup_file(file_path)
                        continue

                    md_result = await converter.convert_to_markdown(file_path)
                    cleanup_file(file_path)
                    if not md_result["success"]:
                        file_result["status"] = "failed"
                        file_result["error"] = md_result["error"]
                        fail_count += 1
                        results.append(file_result)
                        continue
                    md_content = md_result["content"]
                else:
                    # 直接读取 markdown 内容
                    content = await file.read()
                    md_content = content.decode('utf-8')

                # 格式化 format（兼容带点和不带点）
                fmt = output_format if output_format.startswith('.') else '.' + output_format

                # 选择转换器
                fmt_converter = None
                if fmt == ".docx":
                    fmt_converter = DocxConverter()
                elif fmt in [".xlsx", ".xls"]:
                    fmt_converter = ExcelConverter()
                elif fmt == ".pptx":
                    fmt_converter = PPTConverter()
                elif fmt == ".pdf":
                    file_result["status"] = "failed"
                    file_result["error"] = "Markdown转PDF暂未实现"
                    fail_count += 1
                    results.append(file_result)
                    continue

                if not fmt_converter:

                    file_result["status"] = "failed"
                    file_result["error"] = f"未找到 {fmt} 转换器"
                    fail_count += 1
                    results.append(file_result)
                    continue

                # 执行转换
                out_filename = file.filename.rsplit('.', 1)[0] + fmt
                out_path = batch_dir / out_filename
                result_path = await fmt_converter.convert_from_markdown(md_content, out_path)

                file_result["status"] = "success"
                file_result["output"] = out_filename
                success_count += 1
            
        except Exception as e:
            file_result["status"] = "failed"
            file_result["error"] = str(e)
            fail_count += 1
        
        results.append(file_result)
    
    processing_time = round(time.time() - start_time, 2)
    
    # 保存批量转换结果信息
    batch_info = {
        "batch_id": batch_id,
        "total_files": len(files),
        "success_count": success_count,
        "fail_count": fail_count,
        "processing_time": processing_time,
        "output_dir": str(batch_dir),
        "results": results
    }
    
    # 保存结果信息到文件
    info_path = batch_dir / "batch_info.json"
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(batch_info, f, ensure_ascii=False, indent=2)
    
    return {
        "success": True,
        "batch_id": batch_id,
        "total_files": len(files),
        "success_count": success_count,
        "fail_count": fail_count,
        "processing_time": processing_time,
        "results": results
    }


# 4. 下载批量转换结果
@app.get("/convert/batch/download")
async def download_batch_results(batch_id: str = Query(...)):
    """下载批量转换结果的ZIP文件"""
    batch_dir = OUTPUT_DIR / f"batch_{batch_id}"
    
    if not batch_dir.exists():
        raise HTTPException(status_code=404, detail="批量转换结果不存在")
    
    try:
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 添加所有生成的文件
            for file_path in batch_dir.glob('*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.name)
        
        zip_buffer.seek(0)
        
        # 返回ZIP文件
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=converted_files_{batch_id}.zip"
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


# 5. 获取支持格式信息
@app.get("/formats")
async def get_supported_formats():
    """获取所有支持的转换格式"""
    return {
        "to_markdown": [
            {"ext": ext, "name": get_format_name(ext)} 
            for ext in SUPPORTED_CONVERSIONS["to_markdown"]
        ],
        "from_markdown": [
            {"ext": ext, "name": get_format_name(ext)} 
            for ext in SUPPORTED_CONVERSIONS["from_markdown"]
        ],
        "limitations": {
            "image_to_markdown": "需要安装Tesseract-OCR和对应语言包",

            "markdown_to_pdf": "暂未实现，需要额外工具支持"
        }
    }

def get_format_name(ext: str) -> str:
    """获取格式的中文名称"""
    format_names = {
        '.pdf': 'PDF文档',
        '.docx': 'Word文档',
        '.xlsx': 'Excel表格',
        '.xls': 'Excel表格(旧版)',
        '.pptx': 'PowerPoint演示文稿',
        '.jpg': 'JPEG图片',
        '.jpeg': 'JPEG图片',
        '.png': 'PNG图片',
        '.bmp': 'BMP图片',
        '.tiff': 'TIFF图片',
        '.gif': 'GIF图片'
    }
    return format_names.get(ext.lower(), ext.upper())


# 6. 文件清理任务（定期清理临时文件）
import threading
import time

def cleanup_old_files():
    """清理超过1小时的临时文件"""
    current_time = time.time()
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        for file_path in directory.glob('*'):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > 3600:
                    try:
                        file_path.unlink()
                    except:
                        pass


# 7. 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return {
        "success": False,
        "error": "服务器内部错误",
        "detail": str(exc)
    }


if __name__ == "__main__":
    import os
    cleanup_old_files()
    import uvicorn
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8066"))
    uvicorn.run(app, host=host, port=port)
