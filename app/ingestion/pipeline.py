import subprocess
import sys

steps = [

    "ingest_docling.py",

    "ingest_docling_v2.py",

    "extract_docling_images.py",

    "image_ingest.py"
]

for step in steps:

    print(
        f"\nRunning {step}"
    )

    result = subprocess.run(
        [sys.executable, step]
    )

    if result.returncode != 0:

        raise RuntimeError(
            f"{step} failed"
        )

print(
    "\nPipeline Complete"
)