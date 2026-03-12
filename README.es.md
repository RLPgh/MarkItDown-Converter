# MarkItDown Converter (MDTransformer)

<p align="center">
  <img src="assets/icon.png" alt="MarkItDown Converter" width="128">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/flet-0.25.0+-green.svg" alt="Flet 0.25.0+">
  <img src="https://img.shields.io/badge/version-0.1.0-orange.svg" alt="Version 0.1.0">
</p>

*Para la documentación en inglés ver [README.md](README.md)*

Aplicación de escritorio para convertir archivos (PDF, Word, Excel, PowerPoint, HTML, imágenes y más) a formato Markdown usando la librería `markitdown` de Microsoft con procesamiento mejorado de PDFs.

## ✨ Características

- **🔄 Multi-formato**: Convierte PDF, Word, Excel, PowerPoint, HTML, imágenes y más.
- **📁 Escaneo de carpetas**: Agrega todos los archivos soportados de una carpeta.
- **📊 Procesamiento por lotes**: Convierte múltiples archivos con barra de progreso.
- **📄 PDFs mejorados**: Extracción avanzada de tablas con `pymupdf4llm`.
- **📈 Logs en tiempo real**: Monitorea el progreso de las conversiones visualmente.
- **🎨 Interfaz moderna**: UI oscura y elegante con Flet.
- **🚀 Portable y Local**: No requiere internet, todos los archivos se procesan en tu equipo.

## 🚀 Instalación y Uso Rápido

### 1. Uso Diario (Ejecución Rápida)
Haz doble clic en `run.bat`.
Esto abrirá el programa de forma inmediata. Si nunca has usado el programa, este archivo se encargará automáticamente de instalar todo lo necesario antes de abrirse.

### 2. Instalación Manual en Escritorio
Haz doble clic en `install_desktop.bat`.
Esto ejecutará específicamente la descarga del entorno y **creará un acceso directo** en tu escritorio para mayor comodidad.

### 3. Programa Portable Único (.exe)
Puedes descargar directamente el programa compilado `MDTransformer.exe` listo para usar desde la página de **[GitHub Releases](../../releases)**. ¡No requiere instalación!
*(Desarrolladores: También pueden compilarlo manualmente haciendo doble clic en `build_exe.bat`, lo que lo guardará en la carpeta `dist/`).*

## 📁 Estructura y Arquitectura del Proyecto

```text
MDTransformer/
├── main.py                 # Punto de entrada
├── install_desktop.bat     # Instala dependencias y crea el acceso directo
├── run.bat                 # Lanzador de uso diario (sin consola)
├── build_exe.bat           # Compilador portátil (.exe)
├── requirements.txt        # Dependencias vitales
│
├── src/
│   ├── core/               # Lógica y motores
│   │   ├── converter.py    # Servicio markitdown
│   │   ├── controller.py   # Orquestador del estado y operaciones
│   │   ├── pdf_processor.py    # Parser avanzado pymupdf4llm
│   │   ├── post_processor.py   # Limpiador de formato MD
│   │   └── image_processor.py  # Módulo para OCR (Tesseract)
│   │
│   ├── ui/                 
│   │   └── app_layout.py   # Interfaz en Flet
│   │
│   └── utils/
│       └── logger.py       # Configuración asíncrona de Logs
```

##  Créditos y Agradecimientos

Un agradecimiento gigante a los proyectos de código abierto que hacen esto posible:
- [Microsoft markitdown](https://github.com/microsoft/markitdown) - Motor núcleo multi-formato
- [Flet-dev (Flutter for Python)](https://flet.dev/) - Framework increíble para interfaz gráfica de escritorio
- [PyMuPDF4LLM](https://github.com/pymupdf/RAG) - Poderosa extracción de texto y tablas en PDF
