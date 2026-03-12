# MarkItDown Converter (MDTransformer)

<p align="center">
  <img src="assets/icon.png" alt="MarkItDown Converter" width="128">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/flet-0.25.0+-green.svg" alt="Flet 0.25.0+">
  <img src="https://img.shields.io/badge/version-0.1.0-orange.svg" alt="Version 0.1.0">
</p>

*For Spanish documentation see [README.es.md](README.es.md)*

Desktop application to convert files (PDF, Word, Excel, PowerPoint, HTML, images, and more) to Markdown format using Microsoft's `markitdown` library and enhanced PDF processing.

## ✨ Features

- **🔄 Multi-format**: Converts PDF, Word, Excel, PowerPoint, HTML, images, and more.
- **📁 Folder Scan**: Add all supported files from an entire folder.
- **📊 Batch Processing**: Convert multiple files with a progress bar.
- **📄 Enhanced PDFs**: Advanced table extraction and formatting using `pymupdf4llm`.
- **📈 Real-time Logs**: Visual monitoring of conversion progress.
- **🎨 Modern UI**: Sleek dark interface built with Flet.
- **🚀 Portable & Local**: No internet required, all files processed locally.

## 🚀 Quick Start

### 1. Daily Usage (Fast Launch)
Double-click `run.bat`.
This will immediately open the app. If you have never run the program before, it will automatically set up the needed environment first.

### 2. Manual Desktop Setup
Double-click `install_desktop.bat`.
This will specifically create an isolated environment (`venv`), install dependencies, and **create a desktop shortcut** for your convenience.

### 3. Portable Executable (.exe)
You can directly download the compiled, single-file `MDTransformer.exe` from the **[GitHub Releases](../../releases)** page. No installation required!
*(Developers: You can also build it yourself by double-clicking `build_exe.bat` which will pack it into the `dist/` folder).*

## 📁 Project Structure & Architecture

```text
MDTransformer/
├── main.py                 # Application entry point
├── install_desktop.bat     # Installs env & creates shortcut
├── run.bat                 # Fast daily execution
├── build_exe.bat           # Packs the program into a portable .exe
├── requirements.txt        # Production dependencies
│
├── src/
│   ├── core/               # Business logic
│   │   ├── converter.py    # Conversion service (markitdown)
│   │   ├── controller.py   # State management & thread orchestration
│   │   ├── pdf_processor.py    # pymupdf4llm PDF text/table parser
│   │   ├── post_processor.py   # Markdown output cleanup
│   │   └── image_processor.py  # OCR abstraction
│   │
│   ├── ui/                 
│   │   └── app_layout.py   # Flet Desktop Interface (Views)
│   │
│   └── utils/
│       └── logger.py       # Async-safe logging configuration
```

##  Acknowledgements / Credits

A huge thank you to the awesome open-source projects that make this tool possible:
- [Microsoft markitdown](https://github.com/microsoft/markitdown) - Core multiformat engine
- [Flet-dev (Flutter for Python)](https://flet.dev/) - Beautiful Desktop UI framework
- [PyMuPDF4LLM](https://github.com/pymupdf/RAG) - Powerful PDF text & table extraction
