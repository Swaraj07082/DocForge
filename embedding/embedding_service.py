import glob
import json
import pickle
from pathlib import Path

import faiss
from langchain_core.documents import Document
from sentence_transformers import SentenceTransformer

CHUNKED_FILES_GLOB = "./chunked_files/chunked_*.json"
VECTOR_STORE_DIR = Path("./vector_store")
INDEX_PATH = VECTOR_STORE_DIR / "index.faiss"
DOCUMENTS_PATH = VECTOR_STORE_DIR / "documents.pkl"

# Path is preferred over string because Path provides more fuc
# Path("a") / Path("b") is equivalent to Path("a/b")
# Path("a").joinpath("b") is equivalent to Path("a/b")
# Path("a").exists() is equivalent to os.path.exists("a")
# Path("a").is_file() is equivalent to os.path.isfile("a")
# Path("a").is_dir() is equivalent to os.path.isdir("a")
# Path("a").is_symlink() is equivalent to os.path.islink("a")
# Path("a").is_mount() is equivalent to os.path.ismount("a")

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-small-en-v1.5")
    return _model


def load_chunks_and_create_documents(chunk_file: str) -> list[Document]:
    with open(chunk_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    documents: list[Document] = []
    for chunk in data["chunks"]:
        page_content = f"""
        Function : {chunk.get('name', 'Unknown')},
        Type : {chunk.get('kind', 'Unknown')},
       
        
        Code :
        {chunk.get('text', 'No code available')}
"""
        
        metadata = {
            "file": chunk["file"],
            "language": chunk["language"],
            "start_byte": chunk["span"]["start_byte"],
            "end_byte": chunk["span"]["end_byte"],
            "start_line": chunk["span"]["start_line"],
            "end_line": chunk["span"]["end_line"],
        }
        if "parent" in chunk:
            metadata["parent"] = chunk["parent"]
        if "decorators" in chunk:
            metadata["decorators"] = chunk["decorators"]

        documents.append(Document(page_content=page_content, metadata=metadata))

    # print(documents[0])
    return documents


def load_all_documents(pattern: str = CHUNKED_FILES_GLOB) -> list[Document]:
    documents: list[Document] = []
    for chunk_file in sorted(glob.glob(pattern)):
        # sorted(glob.glob(pattern)) is used to ensure that the documents are loaded in the correct order, since glob.glob returns a list of files in arbitrary order , suppose we have the pattern chunked_*.json, then sorted(glob.glob(pattern)) will return a list of files in the correct order like ['chunked_1.json', 'chunked_2.json', 'chunked_3.json']
        documents.extend(load_chunks_and_create_documents(chunk_file))
        # load_chunks_and_create_documents(chunk_file) is used to load the chunks from the chunked_file and create a list of documents and returns a list of documents
        # documents.extend(load_chunks_and_create_documents(chunk_file)) is used to extend the documents list with the list of documents returned by load_chunks_and_create_documents(chunk_file)
        # so documents will be a list of documents from all the chunked files
        # [1, 2, 3] if we extend this to [3, 4] we will get [1, 2, 3, 3, 4]
        # [1, 2, 3] if we append this to [3, 4] we will get [1, 2, 3, [3, 4]]
    return documents


def build_index(documents: list[Document]) -> faiss.IndexFlatIP:
    model = get_model()
    dimension = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatIP(dimension)
    if not documents:
        return index

    texts = [document.page_content for document in documents]
    embeddings = model.encode(texts, convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    return index


def save_vector_store(index: faiss.IndexFlatIP, documents: list[Document]) -> None:
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    with open(DOCUMENTS_PATH, "wb") as f:
        # wb as we are writing a binary file
        pickle.dump(documents, f)
        # converts python object to a binary stream and saves it to the file


def load_vector_store() -> tuple[faiss.IndexFlatIP, list[Document]]:
    index = faiss.read_index(str(INDEX_PATH))
    with open(DOCUMENTS_PATH, "rb") as f:
        documents = pickle.load(f)
        # rb as we are reading a binary file
    return index, documents


if __name__ == "__main__":
    documents = load_all_documents()
    index = build_index(documents)
    save_vector_store(index, documents)
    print(f"Documents: {len(documents)}")
    print(f"Index vectors (ntotal): {index.ntotal}")
    print(f"Aligned: {index.ntotal == len(documents)}")
    print(f"Saved index to: {INDEX_PATH}")
    print(f"Saved documents to: {DOCUMENTS_PATH}")
