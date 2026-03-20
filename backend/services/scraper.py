from urllib.parse import quote_plus
from typing import List, Dict

# In-memory cache (kept for API compatibility)
_SCRAPE_CACHE: Dict[str, List[Dict[str, str]]] = {}


def _build_links(skill: str) -> List[Dict[str, str]]:
    """Instantly build curated search links for a skill — no HTTP requests."""
    q = quote_plus(skill)
    return [
        {
            "title": f"{skill} – freeCodeCamp",
            "url": f"https://www.freecodecamp.org/news/search/?query={q}",
            "source": "freeCodeCamp",
        },
        {
            "title": f"{skill} – GeeksforGeeks",
            "url": f"https://www.geeksforgeeks.org/search/?q={q}",
            "source": "GeeksforGeeks",
        },
        {
            "title": f"{skill} Tutorial – YouTube",
            "url": f"https://www.youtube.com/results?search_query={q}+tutorial",
            "source": "YouTube",
        },
        {
            "title": f"{skill} – Coursera",
            "url": f"https://www.coursera.org/search?query={q}",
            "source": "Coursera",
        },
    ]


async def fetch_resources_for_skills(skills: List[str]) -> Dict[str, List[Dict[str, str]]]:
    """
    Returns a dict mapping each skill name to a list of pre-built resource links.
    Fully synchronous under the hood — returns instantly.
    """
    resource_map: Dict[str, List[Dict[str, str]]] = {}
    for skill in skills:
        key = skill.lower().strip()
        if key not in _SCRAPE_CACHE:
            _SCRAPE_CACHE[key] = _build_links(skill)
        resource_map[key] = _SCRAPE_CACHE[key]
    return resource_map
