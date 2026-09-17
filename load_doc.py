from pathlib import Path
from langchain_community.document_loaders import PyMuPDFLoader, UnstructuredMarkdownLoader

def load_documents(folder_path: Path):
    documents = []

    for file_path in folder_path.rglob("*"):
        suffix = file_path.suffix.lower()

        if suffix == ".pdf":
            loader = PyMuPDFLoader(str(file_path))
        elif suffix == ".md":
            loader = UnstructuredMarkdownLoader(str(file_path))
        else:
            continue

        documents.extend(loader.load())

    return documents