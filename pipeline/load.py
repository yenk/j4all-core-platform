# This script fetches and downloads PDF files from a specified website, organized by year.
# It handles duplicate files and provides feedback on the download process.
# The script is designed to be run as a standalone program.

import os
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

BASE_URL = "https://www.cbca.gov/decisions/cda-cases.html"
start_year = 2015
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
    """Find the HTML table corresponding exactly to a given year heading."""
    for header in soup.find_all("h2"):
        if header.get_text(strip=True) == year:
            return header.find_next("table")
    return None


def extract_pdf_entries(section):
    """Extract PDF links along with their type from a section."""
    entries = []
    for row in section.find_all("tr"):
        cells = row.find_all("td")
        # allow for tables with at least 3 cells (up to 2014 have 4, from 2015 have 5+)
        if len(cells) >= 3:
            link_tag = cells[2].find("a", href=True)
            # use 5th cell for type if present, otherwise default
            doc_type = cells[4].get_text(strip=True) if len(cells) >= 5 else "Decision_Dissmisal_Order"
            if link_tag and link_tag["href"].lower().endswith(".pdf"):
                full_url = urljoin(BASE_URL, link_tag["href"])
                entries.append(
                    {
                        "url": full_url,
                        "type": doc_type or "Decision_Dissmisal_Order"
                    }
                )
    return entries


def download_pdfs(pdf_entries, year):
    """Download PDFs, organized by type within the year folder."""
    downloaded = 0

    for entry in pdf_entries:
        url = entry["url"]
        doc_type = entry["type"]
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
            print(f"✅ Downloaded: {filename} -> {doc_type}")
            downloaded += 1
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")

    print(f"{year}: {downloaded} new files downloaded.")


def main():
    soup = fetch_page()
    for year in YEARS:
        print(f"Processing year: {year}")
        section = find_year_section(soup, year)

        if not section:
            print(f"⚠️ Could not find section for {year}")
            continue

        pdf_entries = extract_pdf_entries(section)
        if not pdf_entries:
            print(f"⚠️ No PDF entries found for {year}")
            continue

        download_pdfs(pdf_entries, year)


if __name__ == "__main__":
    main()
