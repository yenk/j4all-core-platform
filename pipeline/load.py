# This script fetches and downloads PDF files from a specified website, organized by year.
# It handles duplicate files and provides feedback on the download process.
# The script is designed to be run as a standalone program.

import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://www.cbca.gov/decisions/cda-cases.html"
start_year = 2025
end_year = 2025
YEARS = [str(year) for year in range(start_year, end_year + 1)]

# Root data directory
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(DATA_PATH, exist_ok=True)


def fetch_page():
    """Fetch and return the parsed HTML soup from the base URL."""
    response = requests.get(BASE_URL, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.content, "html.parser")


def find_year_section(soup, year):
    """Find the HTML section corresponding to a given year."""
    for tag in soup.find_all(["h1", "h2", "h3", "div"]):
        if year in tag.get_text():
            return tag.find_next("table")
    return None


def extract_pdf_entries(section):
    """Extract PDF links along with their type from a section."""
    entries = []
    for row in section.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) >= 5:
            link_tag = cells[2].find("a", href=True)
            doc_type = cells[4].get_text(strip=True)
            if link_tag and link_tag["href"].endswith(".pdf"):
                full_url = urljoin(BASE_URL, link_tag["href"])
                entries.append({
                    "url": full_url,
                    "type": doc_type  # e.g., Decision, Dismissal, Order
                })
    return entries


def download_pdfs(pdf_entries, year):
    """Download PDFs, organized by type within the year folder."""
    downloaded = 0

    for entry in pdf_entries:
        url = entry["url"]
        doc_type = entry["type"] or "Unknown"
        filename = os.path.basename(url)

        type_dir = os.path.join(DATA_PATH, year, doc_type)
        os.makedirs(type_dir, exist_ok=True)
        filepath = os.path.join(type_dir, filename)

        if os.path.exists(filepath):
            print(f"⏭️ Skipping duplicate: {filename}")
            continue

        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded: {filename} → {doc_type}")
            downloaded += 1
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")

    print(f"📦 {year}: {downloaded} new files downloaded.\n")


def main():
    soup = fetch_page()
    for year in YEARS:
        print(f"🔍 Processing year: {year}")
        section = find_year_section(soup, year)

        if not section:
            print(f"⚠️ Could not find section for {year}\n")
            continue

        pdf_entries = extract_pdf_entries(section)
        if not pdf_entries:
            print(f"⚠️ No PDF entries found for {year}\n")
            continue

        download_pdfs(pdf_entries, year)


if __name__ == "__main__":
    main()