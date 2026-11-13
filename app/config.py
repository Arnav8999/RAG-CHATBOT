import os

PDF_PATH = r"sample.pdf"


PDF_NAME = os.path.basename(PDF_PATH)

PDF_ID = (
    os.path.splitext(PDF_NAME)[0]
    .replace(" ", "_")
    .replace("'", "")
)

DATA_DIR = os.path.join(
    "data",
    PDF_ID
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)