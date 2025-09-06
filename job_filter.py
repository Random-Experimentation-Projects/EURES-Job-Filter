import argparse
import csv
import math
from typing import Dict, List

import requests
from requests.adapters import HTTPAdapter, Retry

API_URL = "https://europa.eu/eures/eures-apps/searchengine/page/jv-search/search"
RESULTS_PER_PAGE = 50
KEYWORDS = ["relocation assistance", "visa sponsorship"]


def create_session() -> requests.Session:
    """Create a requests session with retry and CSRF token."""
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Initial request to obtain XSRF-TOKEN cookie
    session.get(API_URL)
    token = session.cookies.get("XSRF-TOKEN")

    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "X-XSRF-TOKEN": token,
        }
    )
    return session


def fetch_page(session: requests.Session, page: int) -> Dict:
    """Fetch a single page of results."""
    body = {
        "resultsPerPage": RESULTS_PER_PAGE,
        "page": page,
        "sortSearch": "BEST_MATCH",
        "keywords": [{"keyword": "software developer", "specificSearchCode": "EVERYWHERE"}],
        "publicationPeriod": None,
        "occupationUris": [],
        "skillUris": [],
        "requiredExperienceCodes": [],
        "positionScheduleCodes": [],
        "sectorCodes": [],
        "educationAndQualificationLevelCodes": [],
        "positionOfferingCodes": [],
        "locationCodes": ["de", "fi", "fr", "nl"],
        "euresFlagCodes": [],
        "otherBenefitsCodes": [],
        "requiredLanguages": [{"isoCode": "en", "level": "C2"}],
        "minNumberPost": None,
        "sessionId": session.cookies.get("EURES_JVSE_SESSIONID"),
    }
    response = session.post(API_URL, json=body)
    response.raise_for_status()
    return response.json()


def contains_keywords(description: str) -> bool:
    """Check if description contains any of the target keywords."""
    text = description.lower()
    return any(keyword in text for keyword in KEYWORDS)


def flatten_locations(location_map: Dict) -> str:
    locations: List[str] = []
    for locs in location_map.values():
        locations.extend(locs)
    return ",".join(filter(None, locations))


def write_csv(jobs: List[Dict], filename: str, write_header: bool) -> None:
    """Append selected job fields to a CSV file."""
    mode = "w" if write_header else "a"
    with open(filename, mode, newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["id", "title", "description", "employer", "location"]
        )
        if write_header:
            writer.writeheader()
        for job in jobs:
            writer.writerow(
                {
                    "id": job.get("id"),
                    "title": job.get("title"),
                    "description": job.get("description"),
                    "employer": job.get("employer", {}).get("name"),
                    "location": flatten_locations(job.get("locationMap", {})),
                }
            )


def main(max_pages: int | None) -> None:
    session = create_session()
    page = 1
    total_pages: int | None = None
    filename = "filtered_jobs.csv"
    write_header = True

    while True:
        if max_pages and page > max_pages:
            break
        data = fetch_page(session, page)
        if total_pages is None:
            total_records = data.get("numberRecords", 0)
            total_pages = math.ceil(total_records / RESULTS_PER_PAGE)
        jobs = data.get("jvs", [])
        filtered = [job for job in jobs if contains_keywords(job.get("description", ""))]
        write_csv(filtered, filename, write_header)
        write_header = False
        page += 1
        if total_pages and page > total_pages:
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch EURES job listings and filter by keywords.")
    parser.add_argument("--max-pages", type=int, default=None, help="Limit number of pages fetched")
    args = parser.parse_args()
    main(args.max_pages)
