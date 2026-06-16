import fitz
from docling.document_converter import DocumentConverter
import os 
import shutil
from config import PDF_PATH


WINDOW_SIZE = 10
OVERLAP = 2


def get_page_windows(total_pages):

    windows = []

    start = 0

    while start < total_pages:

        end = min(
            start + WINDOW_SIZE,
            total_pages
        )

        windows.append(
            (start, end)
        )

        start += (
            WINDOW_SIZE - OVERLAP
        )

    return windows


# ==================================
# LOAD PDF
# ==================================

pdf = fitz.open(PDF_PATH)

total_pages = len(pdf)

print(
    f"Total Pages: {total_pages}"
)

windows = get_page_windows(
    total_pages
)


TEMP_DIR = "temp_docling"

DOCLING_OUTPUT_DIR = "docling_output"

os.makedirs(
    DOCLING_OUTPUT_DIR,
    exist_ok=True
)

if os.path.exists(TEMP_DIR):

    shutil.rmtree(
        TEMP_DIR
    )

os.makedirs(
    TEMP_DIR,
    exist_ok=True
)

for idx, (start, end) in enumerate(windows):

    temp_pdf = fitz.open()

    for page_num in range(start, end):

        temp_pdf.insert_pdf(
            pdf,
            from_page=page_num,
            to_page=page_num
        )

    temp_path = os.path.join(
        TEMP_DIR,
        f"chunk_{idx}.pdf"
    )

    temp_pdf.save(
        temp_path
    )

    temp_pdf.close()

    print(
        f"Created: {temp_path}"
    )
converter = DocumentConverter()

all_markdown = ""

chunk_files = sorted(
    [
        os.path.join(TEMP_DIR, f)
        for f in os.listdir(TEMP_DIR)
        if f.endswith(".pdf")
    ],
    key=lambda x: int(
        os.path.basename(x)
        .replace("chunk_", "")
        .replace(".pdf", "")
    )
)

print(f"\nProcessing {len(chunk_files)} chunks...")

for i, chunk_file in enumerate(chunk_files, start=1):
    try:
        print(f"\n[{i}/{len(chunk_files)}] Docling: {chunk_file}")

        result = converter.convert(chunk_file)
        markdown = result.document.export_to_markdown()

        chunk_name = os.path.basename(chunk_file).replace(".pdf", ".md")

        with open(
            os.path.join(DOCLING_OUTPUT_DIR, chunk_name),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(markdown)

        print(f"Extracted {len(markdown)} chars")

        all_markdown += "\n\n" + markdown

    except Exception as e:
        print(f"FAILED: {chunk_file}")
        print(e)

    from config import DATA_DIR

    MARKDOWN_PATH = os.path.join(
    DATA_DIR,
    "merged_docling.md"
)

with open(
    MARKDOWN_PATH,
    "w",
    encoding="utf-8"
) as f:
    f.write(all_markdown)

print("\nSaved merged_docling.md")

print(f"Total Markdown Size: {len(all_markdown)}")