import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Set the base URL of the site with the decisions
BASE_URL = "https://www.cbca.gov/decisions/cda-cases.html"  # Replace with the actual URL

# Years to scrape
YEARS = ["2025", "2024", "2023", "2022", "2021"]

# Create a root directory to store PDFs
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data")
os.makedirs(DATA_PATH, exist_ok=True)

# Fetch the page
response = requests.get(BASE_URL, timeout=30)  # Set timeout to 10 seconds
soup = BeautifulSoup(response.content, "html.parser")

# Loop through each year
for year in YEARS:
    year_section = None

    # Find year section by heading or id, e.g., <h2>2025</h2> or <div id="2025">
    for tag in soup.find_all(["h1", "h2", "h3", "div"]):
        if year in tag.get_text():
            year_section = tag.find_next("table")  # Assuming data is in a table under the heading
            break

    if not year_section:
        print(f"⚠️ Could not find section for year {year}")
        continue

    # Get all PDF links in "Appellant" column — assumed to be in <a> tags in table rows
    links = year_section.find_all("a", href=True)
    year_dir = os.path.join(DATA_PATH, year)
    os.makedirs(year_dir, exist_ok=True)

    for link in links:
        href = link["href"]
        if href.endswith(".pdf"):
            pdf_url = urljoin(BASE_URL, href)
            filename = os.path.basename(pdf_url)
            save_path = os.path.join(year_dir, filename)

            # Download the file
            try:
                file_response = requests.get(pdf_url)
                with open(save_path, "wb") as f:
                    f.write(file_response.content)
                print(f"✅ {year}: Downloaded {filename}")
            except Exception as e:
                print(f"❌ Failed to download {filename} from {pdf_url}: {e}")
