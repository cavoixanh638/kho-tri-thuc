"""PDFium permits only one active caller per process, even on separate files."""

from threading import Lock

PDFIUM_LOCK = Lock()
