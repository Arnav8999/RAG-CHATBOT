import os
import pickle
import fitz
from config import PDF_PATH, PDF_NAME
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter
)

from langchain_core.documents import (
    Document
)

from langchain_huggingface import (
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import (
    FAISS
)

from langchain_community.retrievers import (
    BM25Retriever
)

import re



def detect_section(text):

    lines = text.split("\n")

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if line.startswith("## "):

            return line.replace(
                "## ",
                ""
            )

    return "Unknown"

    

def detect_content_type(text):

    pipe_count = text.count("|")

    if pipe_count > 20:
        return "table"

    return "text"
from config import DATA_DIR
FAISS_PATH = os.path.join(
    DATA_DIR,
    "db_vector_docling"
)

BM25_DIR = os.path.join(
    DATA_DIR,
    "db_bm25_docling"
)

os.makedirs(
    BM25_DIR,
    exist_ok=True
)

BM25_PATH = os.path.join(
    BM25_DIR,
    "bm25.pkl"
)

PARENT_STORE = os.path.join(
    DATA_DIR,
    "parent_docs_docling.pkl"
)

PARENT_PAGE_MAP = os.path.join(
    DATA_DIR,
    "parent_page_map.pkl"
)
embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)
parent_splitter = (
    RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=150
    )
)

child_splitter = (
    RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=75
    )
)


MARKDOWN_PATH = os.path.join(
    DATA_DIR,
    "merged_docling.md"
)
pdf = fitz.open(PDF_PATH)

total_pages = len(pdf)

pdf.close()

with open(
    MARKDOWN_PATH,
    "r",
    encoding="utf-8"
) as f:

    text = f.read()
    print(
    "Markdown length:",
    len(text)
)

parent_chunks = parent_splitter.split_text(
    text
)


print(
    f"Parents: {len(parent_chunks)}"
)
parent_docs = {}
parent_page_map = {}

docs = []

for parent_idx, parent_text in enumerate(
    parent_chunks
):

    parent_id = (
        f"parent_{parent_idx}"
    )
    estimated_page = int(
    (
        parent_idx /
        len(parent_chunks)
    )
    * total_pages
) + 1

    parent_page_map[
        parent_id
    ] = estimated_page

    parent_docs[
        parent_id
    ] = parent_text
    section_name = detect_section(
    parent_text
)
    if "Table of Contents" in parent_text:

        continue
    content_type = detect_content_type(
    parent_text
)

    child_chunks = (
        child_splitter.split_text(
            parent_text
        )
    )

    for child_text in child_chunks:

        doc = Document(

            page_content=child_text,

            metadata={

                "parent_id":
                    parent_id,

                "source": PDF_NAME,

                "document_type":
                    "manual",

                "parser":
                    "docling",
                "section":
                    section_name,

                "content_type":
                    content_type,

                "parent_length":
                    len(parent_text)
        }
        )

        docs.append(doc)
        if len(docs) < 3:
            print(doc.metadata)
with open(
    PARENT_STORE,
    "wb"
) as f:

    pickle.dump(
        parent_docs,
        f
    )
with open(
    PARENT_PAGE_MAP,
    "wb"
) as f:

    pickle.dump(
        parent_page_map,
        f
    )
print(
    f"Saved {len(parent_docs)} parents"
)
toc_count = 0

for p in parent_docs.values():

    if "Table of Contents" in p:

        toc_count += 1

print(
    f"TOC chunks found: {toc_count}"
)  
vector_db = (
    FAISS.from_documents(
        docs,
        embeddings
    )
)

vector_db.save_local(
    FAISS_PATH
)

print(
    "FAISS saved"
)
bm25 = (
    BM25Retriever.from_documents(
        docs
    )
)



with open(
    BM25_PATH,
    "wb"
) as f:

    pickle.dump(
        bm25,
        f
    )

print(
    "BM25 saved"
)