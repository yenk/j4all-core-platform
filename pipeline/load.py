# This script fetches and downloads PDF files from a specified website, organized by year.
# It handles duplicate files and provides feedback on the download process.
# The script is designed to be run as a standalone program.

import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://www.cbca.gov/decisions/cda-cases.html"
YEARS = ["2025", "2024", "2023", "2022", "2021"]

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


def extract_pdf_links(section):
    """Extract all PDF links from a given section."""
    return [
        urljoin(BASE_URL, link["href"])
        for link in section.find_all("a", href=True)
        if link["href"].endswith(".pdf")
    ]


def download_pdfs(pdf_urls, year):
    """Download PDF files for a given year, skipping duplicates."""
    year_dir = os.path.join(DATA_PATH, year)
    os.makedirs(year_dir, exist_ok=True)

    downloaded = 0
    for url in pdf_urls:
        filename = os.path.basename(url)
        filepath = os.path.join(year_dir, filename)

        if os.path.exists(filepath):
            print(f"⏭️ Skipping duplicate: {filename}")
            continue

        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"✅ Downloaded: {filename}")
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

        pdf_links = extract_pdf_links(section)
        if not pdf_links:
            print(f"⚠️ No PDF links found for {year}\n")
            continue

        download_pdfs(pdf_links, year)


if __name__ == "__main__":
    main()
