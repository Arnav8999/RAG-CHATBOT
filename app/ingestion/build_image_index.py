import os
import pickle

from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from config import PDF_NAME

# =========================
# LOAD IMAGE METADATA
# =========================

from config import DATA_DIR

IMAGE_METADATA = os.path.join(
    DATA_DIR,
    "image_metadata.pkl"
)

with open(
    IMAGE_METADATA,
    "rb"
) as f:

    images = pickle.load(f)

print(
    f"Loaded {len(images)} images"
)

# =========================
# EMBEDDINGS
# =========================

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5"
)

# =========================
# BUILD DOCUMENTS
# =========================

docs = []

for image in images:

    caption = image.get(
        "caption",
        ""
    )

    if not caption:
        continue

    docs.append(
        Document(
            page_content=caption,
            metadata={
                "source": PDF_NAME,
                "image_path":
                    image["image_path"],

                "page":
                    image["page"],

                "caption":
                    caption
            }
        )
    )

print(
    f"Captioned images: {len(docs)}"
)

# =========================
# CREATE FAISS
# =========================

IMAGE_FAISS = os.path.join(
    DATA_DIR,
    "db_image_faiss"
)

if len(docs) == 0:

    print(
        "No captioned images found."
    )

    exit()
db = FAISS.from_documents(
    docs,
    embeddings
)
db.save_local(
    IMAGE_FAISS
)

print(
    "Saved image FAISS index"
)