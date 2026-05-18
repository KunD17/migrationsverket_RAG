"""
Pull the real URL list from migrationsverket.se's sitemap and report
how many pages cover topics relevant to a researcher living and working in Sweden.
"""

import gzip
import re
import requests
from migrationsverket_bot.config import USER_AGENT

HEADERS = {"User-Agent": USER_AGENT}
SITEMAP_URL = "https://www.migrationsverket.se/sitemap1.xml.gz"

RELEVANT_KEYWORDS = [
    # Work / high-skill
    "work", "arbeta", "arbetstillstand", "work-permit",
    "highly-qualified", "hogkvalificerad",
    "eu-blue-card", "blue-card",
    "researcher", "forskar",
    "self-employ", "eget-foretag",
    "intracompany", "ict-permit",
    "specialist",
    # Study
    "studi", "study", "student",
    "jobseeker", "jobbsokare",
    # Extending / changing permits
    "extend", "forlanga", "renew",
    "change-condition", "andra-villkor",
    # Long-term
    "permanent", "PUT",
    "citizenship", "medborgarskap",
    # Family
    "family-reunif", "familjeaterforening",
    "family-member",
    # Visiting
    "visit", "besoka", "besok",
    "invite", "bjuda",
    "schengen", "visering",
]

print(f"Fetching sitemap from {SITEMAP_URL}...")
response = requests.get(SITEMAP_URL, headers=HEADERS, timeout=30)
response.raise_for_status()

xml = gzip.decompress(response.content).decode("utf-8")
all_urls = re.findall(r"<loc>(https://[^<]+)</loc>", xml)
print(f"Total URLs in sitemap: {len(all_urls)}\n")

def is_relevant(url: str) -> bool:
    url_lower = url.lower()
    return any(kw in url_lower for kw in RELEVANT_KEYWORDS)

relevant = [u for u in all_urls if is_relevant(u)]
print(f"Relevant to your topics: {len(relevant)} pages\n")

# Break down by topic
topics = {
    "Work / high-skill":        ["work", "arbeta", "arbetstillstand"],
    "Highly qualified":         ["highly-qualified", "hogkvalificerad", "specialist"],
    "EU Blue Card":             ["eu-blue-card", "blue-card"],
    "Researcher":               ["researcher", "forskar"],
    "Studying":                 ["studi", "study", "student"],
    "Study → job seeker":       ["jobseeker", "jobbsokare"],
    "Extend / change permit":   ["extend", "forlanga", "change-condition", "andra-villkor"],
    "Permanent residency":      ["permanent"],
    "Citizenship":              ["citizenship", "medborgarskap"],
    "Family reunification":     ["family-reunif", "familjeaterforening"],
    "Visiting / inviting":      ["visit", "besoka", "invite", "bjuda"],
    "Schengen / visa":          ["schengen", "visering"],
}

for label, keywords in topics.items():
    count = sum(1 for u in all_urls if any(kw in u.lower() for kw in keywords))
    if count:
        print(f"  {label:<30} {count} pages")

print("\nSample relevant URLs:")
for url in relevant[:20]:
    print(f"  {url}")
if len(relevant) > 20:
    print(f"  ... and {len(relevant) - 20} more")