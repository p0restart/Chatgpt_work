from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


HERE = Path(__file__).resolve().parent
SOURCE = Path(r"C:\Users\Jin\Desktop\Analysis of attack-defense game for advanced malware propagation control in cloud.pdf")
OUTPUT = HERE / "Analysis_of_attack_defense_game_2025_中文全文翻译.pdf"
REVIEWS = HERE / "reviews" / "page_checks.json"
EXPECTED_SHA256 = "414d3b0683bb3d41c0e59f7c7931ccc4b4b1c8000c57956ce9dac7eec923f474"


def main() -> None:
    task = json.loads((HERE / "task.json").read_text(encoding="utf-8"))
    source_hash = task["source"]["sha256"]
    if source_hash != EXPECTED_SHA256:
        raise RuntimeError("Saved source hash mismatch")
    if SOURCE.is_file() and hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED_SHA256:
        raise RuntimeError("Source PDF changed")
    page_count = task["source"]["page_count"]
    page_sizes = [task["pages"][str(i)]["source_page_size"] for i in range(1, page_count + 1)]
    for i in range(1, page_count + 1):
        source_image = HERE / task["pages"][str(i)]["input"]
        if hashlib.sha256(source_image.read_bytes()).hexdigest() != task["pages"][str(i)]["input_sha256"]:
            raise RuntimeError(f"Saved source page {i} changed")
    reviews = json.loads(REVIEWS.read_text(encoding="utf-8"))
    if reviews["source_sha256"] != source_hash:
        raise RuntimeError("Review does not match source")
    checks = reviews["checks"]
    if page_count != 12 or [c["page"] for c in checks] != list(range(1, 13)):
        raise RuntimeError("Page count or review mapping mismatch")
    if any(c["status"] not in {"pass", "issue", "unknown"} or not c["observations"] for c in checks):
        raise RuntimeError("Missing page review")

    temp = OUTPUT.with_suffix(".building.pdf")
    pdf = canvas.Canvas(str(temp), pageCompression=1)
    for number, (width, height) in enumerate(page_sizes, start=1):
        image_path = HERE / "translated_pages" / f"page-{number:02}.png"
        if not image_path.is_file():
            raise RuntimeError(f"Missing translated page {number}")
        width = float(width)
        height = float(height)
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            image_width, image_height = image.size
            scale = min(width / image_width, height / image_height)
            drawn_width, drawn_height = image_width * scale, image_height * scale
            pdf.setPageSize((width, height))
            pdf.drawImage(
                ImageReader(image),
                (width - drawn_width) / 2,
                (height - drawn_height) / 2,
                width=drawn_width,
                height=drawn_height,
            )
            pdf.showPage()
    pdf.save()

    result = PdfReader(str(temp))
    if len(result.pages) != page_count:
        raise RuntimeError("Assembled page count mismatch")
    for number, ((width, height), translated) in enumerate(zip(page_sizes, result.pages), start=1):
        if abs(float(width) - float(translated.mediabox.width)) > 0.01:
            raise RuntimeError(f"Width mismatch on page {number}")
        if abs(float(height) - float(translated.mediabox.height)) > 0.01:
            raise RuntimeError(f"Height mismatch on page {number}")
        xobjects = translated["/Resources"].get("/XObject")
        if not xobjects:
            raise RuntimeError(f"No image on page {number}")
    temp.replace(OUTPUT)
    print(OUTPUT)
    print(f"pages={len(result.pages)} size={OUTPUT.stat().st_size}")
    print("review_unknown=" + ",".join(str(c["page"]) for c in checks if c["status"] == "unknown"))


if __name__ == "__main__":
    main()
