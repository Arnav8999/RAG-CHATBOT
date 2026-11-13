import os
import pickle

import fitz
from config import PDF_PATH
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import PictureItem, TextItem
from config import DATA_DIR

# =====================================
# CONFIG
# =====================================


BATCH_SIZE = 15
IMAGE_DIR = os.path.join(
    DATA_DIR,
    "docling_images"
)
METADATA_FILE = os.path.join(
    DATA_DIR,
    "image_metadata.pkl"
)
TEMP_DIR = os.path.join(
    DATA_DIR,
    "temp_docling_images"
)

os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)


# =====================================
# LOAD PDF
# =====================================

pdf = fitz.open(PDF_PATH)
total_pages = len(pdf)

print(f"Total Pages: {total_pages}")


# =====================================
# DOCLING CONFIG
# =====================================

pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False
pipeline_options.images_scale = 1.0
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)


# =====================================
# STORAGE
# =====================================

image_metadata = []
picture_count = 0


def _looks_like_caption(text):
    if not text:
        return False

    lowered = text.strip().lower()
    caption_keywords = ["figure", "fig.", "table", "diagram", "image"]

    return any(lowered.startswith(keyword) for keyword in caption_keywords)


# =====================================
# PROCESS PDF IN BATCHES
# =====================================

for start_page in range(0, total_pages, BATCH_SIZE):

    end_page = min(start_page + BATCH_SIZE, total_pages)

    print(f"\nProcessing pages {start_page + 1}-{end_page}")

    temp_pdf = fitz.open()
    temp_pdf.insert_pdf(
        pdf,
        from_page=start_page,
        to_page=end_page - 1,
    )

    temp_path = os.path.join(
        TEMP_DIR,
        f"batch_{start_page + 1}_{end_page}.pdf",
    )

    temp_pdf.save(temp_path)
    temp_pdf.close()

    try:
        result = converter.convert(temp_path)
        items = list(result.document.iterate_items())

        for i, (element, _level) in enumerate(items):
            if not isinstance(element, PictureItem):
                continue

            try:
                img = element.get_image(result.document)

                if img is None:
                    continue

                filename = f"picture_{picture_count}.png"
                image_path = os.path.join(IMAGE_DIR, filename)
                img.save(image_path)

                try:
                    caption = element.caption_text(
                        result.document
                    )

                    if caption:
                        caption = caption.strip()

                        if len(caption) > 300:
                            caption = ""
                except Exception:
                    caption = ""

                if not caption and i + 1 < len(items):
                    next_el, _ = items[i + 1]
                    if isinstance(next_el, TextItem):
                        text = next_el.text.strip()
                        if _looks_like_caption(text):
                            caption = text

                if not caption and i - 1 >= 0:
                    prev_el, _ = items[i - 1]
                    if isinstance(prev_el, TextItem):
                        text = prev_el.text.strip()
                        if _looks_like_caption(text):
                            caption = text
                if caption:
                    print(
        f"Caption found: {caption}"
    )
                try:
                    page_no = (
                            start_page +
                            element.prov[0].page_no
                            - 1
                        )
                except Exception:
                    page_no = -1

                image_metadata.append(
                    {
                        "ref": element.self_ref,
                        "page": page_no,
                        "caption": caption,
                        "image_path": image_path,
                    }
                )

                picture_count += 1
                print(f"Saved: {filename}")

            except Exception as e:
                print(f"Image error: {e}")

    except Exception as e:
        print(f"Batch failed: {e}")

    try:
        os.remove(temp_path)
    except Exception:
        pass


# =====================================
# SAVE METADATA
# =====================================

with open(METADATA_FILE, "wb") as f:
    pickle.dump(image_metadata, f)

print(f"\nSaved {picture_count} images")
print(f"Metadata -> {METADATA_FILE}")
