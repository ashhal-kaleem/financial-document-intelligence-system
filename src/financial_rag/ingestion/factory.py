"""Factory that selects the correct loader based on file extension."""

from pathlib import Path

from financial_rag.ingestion.base import BaseLoader
from financial_rag.ingestion.models import Document

_REGISTRY: dict[str, type[BaseLoader]] = {}


def register_loader(extension: str):
    """Decorator to register a loader class for a file extension."""
    def decorator(cls: type[BaseLoader]) -> type[BaseLoader]:
        _REGISTRY[extension.lower()] = cls
        return cls
    return decorator


def _build_registry() -> None:
    """Lazily import and register all loaders."""
    if _REGISTRY:
        return
    from financial_rag.ingestion.text_loader import TextLoader
    from financial_rag.ingestion.pdf_loader import PDFLoader

    _REGISTRY[".txt"] = TextLoader
    _REGISTRY[".md"] = TextLoader
    _REGISTRY[".pdf"] = PDFLoader


def load_document(path: str | Path) -> list[Document]:
    """Load a file using the appropriate loader.

    Args:
        path: Path to the document file.

    Returns:
        List of Document objects extracted from the file.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    _build_registry()
    path = Path(path)
    extension = path.suffix.lower()

    if extension not in _REGISTRY:
        supported = ", ".join(sorted(_REGISTRY.keys()))
        raise ValueError(
            f"Unsupported file type: '{extension}'. Supported: {supported}"
        )

    loader_cls = _REGISTRY[extension]
    loader = loader_cls(path)
    return loader.load()


def load_directory(directory: str | Path, recursive: bool = False) -> list[Document]:
    """Load all supported documents from a directory.

    Args:
        directory: Path to the directory.
        recursive: If True, search subdirectories as well.

    Returns:
        Combined list of Documents from all loaded files.
    """
    _build_registry()
    directory = Path(directory)

    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    pattern = "**/*" if recursive else "*"
    documents: list[Document] = []
    errors: list[str] = []

    for file_path in sorted(directory.glob(pattern)):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in _REGISTRY:
            continue
        try:
            docs = load_document(file_path)
            documents.extend(docs)
            print(f"  [loaded] {file_path.name} → {len(docs)} document(s)")
        except Exception as exc:
            errors.append(f"{file_path.name}: {exc}")
            print(f"  [error]  {file_path.name}: {exc}")

    if errors:
        print(f"\n  {len(errors)} file(s) failed to load.")

    return documents
