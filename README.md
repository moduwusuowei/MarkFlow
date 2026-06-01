# 📄 MarkFlow

<div align="center">

**Multi-format Document Converter**

*PDF • Word • Excel • PPT • Images ↔ Markdown*

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=flat-square&logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

</div>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📤 **Document → Markdown** | PDF, Word, Excel, PPT, Images → Markdown |
| 📥 **Markdown → Document** | Markdown → Word, Excel, PPT, PDF |
| 📦 **Batch Conversion** | Convert multiple files at once |
| 🖼️ **OCR Support** | Extract text from images (RapidOCR) |
| 🎨 **Modern UI** | Dark theme, glass morphism, smooth animations |
| 📝 **Conversion History** | Local history saved in browser |
| 🐳 **Docker Ready** | One-click deployment |

## 🚀 Quick Start

### Option 1: Run Locally

```bash
# Clone
git clone https://github.com/moduwusuowei/MarkFlow.git
cd MarkFlow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
```

Open http://localhost:8066

### Option 2: Docker

```bash
# Build and run
docker build -t markflow .
docker run -d -p 8066:8066 markflow

# Or use docker-compose
docker-compose up -d
```

## 📁 Project Structure

```
MarkFlow/
├── main.py              # FastAPI backend + API routes
├── templates/
│   └── index.html       # Frontend (HTML/CSS/JS)
├── converters/          # Document converters
│   ├── __init__.py
│   ├── base.py          # Base converter class
│   ├── pdf_converter.py
│   ├── docx_converter.py
│   ├── excel_converter.py
│   ├── ppt_converter.py
│   └── image_converter.py
├── tests/               # Test files
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .gitignore
└── LICENSE
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8066` | Server port |

### Supported Formats

**Input → Output**

| Input | Output |
|-------|--------|
| PDF | Markdown |
| Word (.docx) | Markdown, Word |
| Excel (.xlsx/.xls) | Markdown, Excel |
| PPT (.pptx) | Markdown, PPT |
| Images (jpg/png/bmp/tiff/gif) | Markdown (OCR) |

## 🛠️ Tech Stack

- **Backend**: FastAPI + Uvicorn
- **Document Processing**: python-docx, openpyxl, python-pptx, PyPDF2
- **Markdown**: markitdown (Microsoft)
- **OCR**: RapidOCR (onnxruntime)
- **Frontend**: Vanilla HTML/CSS/JS (no framework)

## 📡 API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Web UI |
| POST | `/convert/to-markdown` | Document → Markdown |
| POST | `/convert/from-markdown` | Markdown → Document |
| POST | `/convert/batch` | Batch conversion |
| GET | `/convert/batch/download` | Download batch results |
| GET | `/formats` | List supported formats |

Swagger docs: http://localhost:8066/docs

## 🤝 Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- [markitdown](https://github.com/microsoft/markitdown) - Microsoft's document conversion library
- [RapidOCR](https://github.com/RapidAI/RapidOCR) - Lightweight OCR engine
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
