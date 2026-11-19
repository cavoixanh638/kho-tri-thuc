"""Render selected corpus pages outside Git for independent visual QA anchors."""

import argparse
import json
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if output == repository or repository in output.parents:
        raise ValueError("Rendered source pages must stay outside Git")
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(
        Path(__file__).with_name("sources.json").read_text(encoding="utf-8")
    )
    sheet = None
    for index, document in enumerate(manifest["documents"]):
        pdf = pdfium.PdfDocument(args.cache / (document["sha256"] + ".pdf"))
        page_number = min(4, len(pdf))
        page = pdf[page_number - 1]
        image = page.render(scale=1.7).to_pil().convert("RGB")
        image.save(output / f"{document['id']}-page{page_number}.png")
        # Top70% provides legible headings/body while retaining columns/order.
        image = image.crop((0, 0, image.width, int(image.height * 0.7)))
        image.thumbnail((1000, 1000))
        if index % 4 == 0:
            sheet = Image.new("RGB", (2020, 2070), "white")
        x, y = index % 2 * 1010, (index % 4 // 2) * 1035
        sheet.paste(image, (x, y + 28))
        ImageDraw.Draw(sheet).text(
            (x + 5, y + 5),
            f"{document['id']} physical page {page_number}",
            fill="black",
        )
        if index % 4 == 3 or index == len(manifest["documents"]) - 1:
            sheet.save(output / f"contact-{index // 4 + 1}.png")
        page.close()
        pdf.close()


if __name__ == "__main__":
    main()
