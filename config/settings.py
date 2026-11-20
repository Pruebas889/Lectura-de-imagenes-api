import os
import shutil
from glob import glob

#BASE_DIR es la ruta absoluta de la carpeta raiz del proyecto
#os.path.dirname obtiene "la carpeta que contiene este archivo"
#__file__ es la ruta de settings.py
# se hace dos veces para subir dos niveles: de config/ a proyecto_facturas/

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#carpeta donde se guardan los pdfs

PDF_FOLDER = os.path.join(BASE_DIR, "pdfs")
DOCUMENT_FOLDER = os.environ.get("DOCUMENT_FOLDER") or os.path.join(
    BASE_DIR,
    "documentos"
)

DB_PATH = os.path.join(BASE_DIR, "database", "facturas.db")

# Motor de base de datos: sqlite (predeterminado) o mysql.
DB_ENGINE = os.environ.get("DB_ENGINE", "sqlite").strip().lower()

MYSQL_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "lectura_ocr")
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")


TESSERACT_PATH = os.environ.get("TESSERACT_PATH") or shutil.which("tesseract")
if not TESSERACT_PATH:
    for tesseract_dir in (
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Tesseract-OCR"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Tesseract-OCR"),
    ):
        candidate = os.path.join(tesseract_dir, "tesseract.exe")
        if os.path.isfile(candidate):
            TESSERACT_PATH = candidate
            break

POPPLER_PATH = os.environ.get("POPPLER_PATH")
if not POPPLER_PATH:
    pdftoppm_path = shutil.which("pdftoppm")
    POPPLER_PATH = os.path.dirname(pdftoppm_path) if pdftoppm_path else None
if not POPPLER_PATH:
    winget_poppler_paths = glob(
        os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Microsoft", "WinGet", "Packages", "oschwartz10612.Poppler_*",
            "poppler-*", "Library", "bin"
        )
    )
    if winget_poppler_paths:
        POPPLER_PATH = max(winget_poppler_paths, key=os.path.getmtime)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL_TEXTO = "llama-3.3-70b-versatile"
GROQ_MODEL_VISION = "meta-llama/llama-4-scout-17b-16e-instruct"

MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 100 * 1024 * 1024))
if MAX_UPLOAD_BYTES < 1:
    raise ValueError("MAX_UPLOAD_BYTES debe ser mayor que cero.")
