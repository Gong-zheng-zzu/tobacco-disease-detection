"""Collect publisher-labeled tobacco deficiency images for manual review.

These images are research candidates, not a licensed or expert-verified training set.
"""

import csv
import hashlib
import io
import time
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "tobacco_deficiency_candidates"
PAGES = [
    ("ncsu", "N", "https://content.ces.ncsu.edu/tobacco-nitrogen-deficiency"),
    ("ncsu", "P", "https://content.ces.ncsu.edu/tobacco-phosphorus-p-deficiency"),
    ("ncsu", "K", "https://content.ces.ncsu.edu/tobacco-potassium-deficiency"),
    ("uky", "K", "https://burleytobaccoextension.mgcafe.uky.edu/content/potassium-deficiency"),
    ("yara", "N", "https://www.yara.ph/crop-nutrition/tobacco/nutrient-deficiencies-tobacco/nitrogen-deficiency-tobacco/"),
    ("yara", "P", "https://www.yara.ph/crop-nutrition/tobacco/nutrient-deficiencies-tobacco/phosphorus-deficiency-tobacco/"),
    ("yara", "K", "https://www.yara.ph/crop-nutrition/tobacco/nutrient-deficiencies-tobacco/potassium-deficiency-tobacco/"),
    ("inrae", "P", "https://ephytia.inrae.fr/en/C/10967/Tobacco-Nutritional-deficiencies"),
    ("inrae", "K", "https://ephytia.inrae.fr/en/C/10967/Tobacco-Nutritional-deficiencies"),
]
FIELDS = ["file", "label", "source", "page_url", "image_url", "caption", "width", "height", "sha256", "review_status", "rights_status"]


def candidates(source, label, page_url, soup):
    if source == "ncsu":
        for img in soup.select('img[src^="/media/images/"]'):
            yield urljoin(page_url, img["src"]), img.get("alt", "")
    elif source == "uky":
        for img in soup.select("img[alt]"):
            if "potassium" in img["alt"].lower():
                yield urljoin(page_url, img.get("src", "")), img["alt"]
    elif source == "yara":
        for slide in soup.select(".carousel-item"):
            image = slide.select_one("[data-bg]")
            if image:
                title = slide.select_one("h2")
                caption = title.get_text(" ", strip=True) if title else ""
                yield urljoin(page_url, image["data-bg"]), caption
    elif source == "inrae":
        terms = ("carencep", "phospore") if label == "P" else ("carencek", "potassium")
        for img in soup.select("img[src]"):
            alt = img.get("alt", "")
            if any(term in alt.lower() for term in terms):
                yield urljoin(page_url, img["src"]), alt


def main():
    OUTPUT.mkdir(exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "TobaccoResearchImageAudit/1.0 (educational dataset audit)"
    rows = []
    seen = set()
    for source, label, page_url in PAGES:
        page_cache = OUTPUT / f"_page_{source}_{label}.html"
        try:
            for attempt in range(3):
                try:
                    response = session.get(page_url, timeout=25)
                    response.raise_for_status()
                    page_cache.write_text(response.text, encoding="utf-8")
                    break
                except requests.RequestException:
                    if attempt == 2:
                        raise
                    time.sleep(attempt + 1)
            soup = BeautifulSoup(page_cache.read_text(encoding="utf-8"), "html.parser")
        except requests.RequestException as exc:
            if page_cache.exists():
                print(f"PAGE USING CACHE {page_url}", flush=True)
                soup = BeautifulSoup(page_cache.read_text(encoding="utf-8"), "html.parser")
            else:
                print(f"PAGE FAILED {page_url}: {exc}", flush=True)
                continue
        image_urls = dict(candidates(source, label, page_url, soup))
        print(f"PAGE {source} {label}: {len(image_urls)} candidate URLs", flush=True)
        for index, (image_url, caption) in enumerate(image_urls.items(), 1):
            try:
                try:
                    image_response = session.get(image_url, timeout=30)
                    image_response.raise_for_status()
                    raw = image_response.content
                except requests.RequestException:
                    cached = list((OUTPUT / label).glob(f"{source}_{label}_{index:02d}.*"))
                    if not cached:
                        raise
                    raw = cached[0].read_bytes()
                    print(f"USING CACHE {cached[0]}", flush=True)
                with Image.open(io.BytesIO(raw)) as image:
                    image.verify()
                with Image.open(io.BytesIO(raw)) as image:
                    width, height = image.size
                    image_format = image.format.lower()
                if width < 200 or height < 200:
                    print(f"SKIP SMALL {image_url}", flush=True)
                    continue
                digest = hashlib.sha256(raw).hexdigest()
                if digest in seen:
                    continue
                seen.add(digest)
                extension = "jpg" if image_format == "jpeg" else image_format
                filename = f"{source}_{label}_{index:02d}.{extension}"
                folder = OUTPUT / label
                folder.mkdir(exist_ok=True)
                (folder / filename).write_bytes(raw)
                rows.append({
                    "file": f"{label}/{filename}", "label": label, "source": source,
                    "page_url": page_url, "image_url": image_url, "caption": caption,
                    "width": width, "height": height, "sha256": digest,
                    "review_status": "publisher_label_unverified",
                    "rights_status": "reuse_permission_unverified",
                })
            except (requests.RequestException, OSError, ValueError) as exc:
                print(f"IMAGE FAILED {image_url}: {exc}", flush=True)

    with (OUTPUT / "manifest.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter(row["label"] for row in rows)
    print(f"SAVED {len(rows)} unique images: N={counts['N']}, P={counts['P']}, K={counts['K']}", flush=True)


if __name__ == "__main__":
    main()
