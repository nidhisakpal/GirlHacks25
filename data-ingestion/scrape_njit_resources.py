# scraper_search_service.py
import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup
from robotexclusionrulesparser import RobotExclusionRulesParser

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------------------
# If you already have app.models.Citation, delete this dataclass and import yours.
# ---------------------------------------------------------------------
@dataclass
class Citation:
    id: str
    title: str
    url: str
    source: str
    snippet: str
    retrieved: Optional[str] = None


# ---------------------------------------------------------------------
# Utility: robots.txt check (cached per-origin)
# ---------------------------------------------------------------------
class RobotsCache:
    def __init__(self, user_agent: str = "MyScraperBot/1.0 (+contact@example.com)"):
        self.user_agent = user_agent
        self._cache: Dict[str, RobotExclusionRulesParser] = {}
        self._lock = asyncio.Lock()

    async def allowed(self, client: httpx.AsyncClient, url: str) -> bool:
        parsed = urlparse(url)
        robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))

        async with self._lock:
            parser = self._cache.get(robots_url)
            if parser is None:
                parser = RobotExclusionRulesParser()
                try:
                    r = await client.get(robots_url, timeout=10)
                    if r.status_code == 200 and r.text:
                        parser.parse(r.text)
                    else:
                        # No robots or not accessible → default allow
                        parser = None
                except Exception:
                    parser = None
                self._cache[robots_url] = parser  # may be None

        if parser is None:
            return True
        return parser.is_allowed(self.user_agent, url)


# ---------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------
class WebScraper:
    """
    Async scraper that:
      - Respects robots.txt
      - Applies polite concurrency & rate limiting
      - Extracts title/description/date/text
    """

    def __init__(
        self,
        user_agent: str = "MyScraperBot/1.0 (+contact@example.com)",
        max_concurrency: int = 5,
        per_host_delay: float = 1.0,  # seconds between hits to same host
    ) -> None:
        self.user_agent = user_agent
        self.sem = asyncio.Semaphore(max_concurrency)
        self.per_host_delay = per_host_delay
        self._last_hit: Dict[str, float] = {}
        self.robots = RobotsCache(user_agent=user_agent)

        # Simple per-host politeness lock
        self._host_locks: Dict[str, asyncio.Lock] = {}

    def _host_lock(self, host: str) -> asyncio.Lock:
        if host not in self._host_locks:
            self._host_locks[host] = asyncio.Lock()
        return self._host_locks[host]

    async def _polite_wait(self, host: str) -> None:
        lock = self._host_lock(host)
        async with lock:
            now = time.time()
            last = self._last_hit.get(host, 0)
            wait = self.per_host_delay - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_hit[host] = time.time()

    @staticmethod
    def _normalize_url(base: str, href: Optional[str]) -> Optional[str]:
        if not href:
            return None
        href = href.strip()
        if href.startswith("#") or href.lower().startswith("javascript:"):
            return None
        try:
            if bool(urlparse(href).netloc):
                return href
            return urljoin(base, href)
        except Exception:
            return None

    @staticmethod
    def _clean_text(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _extract_metadata(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
        # Title
        title = (soup.title.string if soup.title and soup.title.string else "") or ""
        title = WebScraper._clean_text(title)

        # Description
        desc = ""
        for key in ["description", "og:description", "twitter:description"]:
            tag = soup.find("meta", attrs={"name": key}) or soup.find("meta", attrs={"property": key})
            if tag and tag.get("content"):
                desc = WebScraper._clean_text(tag["content"])
                if desc:
                    break

        # retrieved-ish date (best effort)
        date = None
        for key in ["article:retrieved_time", "og:updated_time", "date"]:
            tag = soup.find("meta", attrs={"name": key}) or soup.find("meta", attrs={"property": key})
            if tag and tag.get("content"):
                date = tag["content"].strip()
                break

        # Canonical URL
        canon = None
        link_tag = soup.find("link", rel="canonical")
        if link_tag and link_tag.get("href"):
            canon = link_tag["href"].strip()

        return {"title": title, "description": desc, "retrieved": date, "canonical": canon}

    @staticmethod
    @staticmethod
    def _extract_main_text(soup: BeautifulSoup, preferred_div_id: str = "block-system-main") -> str:
  
     container = soup.find(id=preferred_div_id)
     if container is None:
         container = soup.body

     chunks = []
     if container:
         for el in container.find_all(["p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "span"]):
            txt = el.get_text(" ", strip=True)
            if txt:
                chunks.append(txt)

     text = " ".join(chunks)
    # collapse whitespace
     return re.sub(r"\s+", " ", text).strip()


    async def fetch(self, client: httpx.AsyncClient, url: str) -> Optional[Dict[str, Any]]:
        parsed = urlparse(url)
        if not parsed.scheme.startswith("http"):
            return None

        # robots.txt
        allowed = await self.robots.allowed(client, url)
        if not allowed:
            LOGGER.info("Blocked by robots.txt: %s", url)
            return None

        # politeness per host
        await self._polite_wait(parsed.netloc)

        # guarded concurrency
        async with self.sem:
            try:
                r = await client.get(url, timeout=20)
            except Exception as e:
                LOGGER.warning("Request failed: %s (%s)", url, e)
                return None

        if r.status_code >= 400:
            LOGGER.info("Non-OK status %s for %s", r.status_code, url)
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        meta = self._extract_metadata(soup)
        #text = self._extract_main_text(soup)
        if ".njit.edu" in parsed.netloc:
         text = self._extract_main_text(soup, preferred_div_id="block-system-main")
        else:
         text = self._extract_main_text(soup, preferred_div_id=None)


        final_url = meta.get("canonical") or str(r.url)

        return {
            "id": final_url,
            "title": meta["title"] or final_url,
            "url": final_url,
            "source": urlparse(final_url).netloc,
            "description": meta["description"] or text[:300],
            "retrieved": meta["retrieved"],
            "tags": [],
            "text": text,
        }

    async def scrape(self, urls: Iterable[str]) -> List[Dict[str, Any]]:
        headers = {"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"}
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            tasks = [self.fetch(client, u) for u in urls]
            results = await asyncio.gather(*tasks)
        return [r for r in results if r]


# ---------------------------------------------------------------------
# SearchService (scrapes first if corpus missing/outdated, then searches)
# ---------------------------------------------------------------------
class SearchService:
    """
    Hybrid search backed by a local scraped corpus (JSON).
    API stays similar to your original SearchService.search(query, intent).
    """

    def __init__(self, corpus_path: Path = Path("data-ingestion/njit_resources.json")) -> None:
        self.corpus_path = corpus_path
        self._fallback_corpus = self._load_corpus()

    def _load_corpus(self) -> List[dict]:
        if not self.corpus_path.exists():
            LOGGER.warning("Corpus not found at %s", self.corpus_path)
            return []
        try:
            with self.corpus_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            LOGGER.warning("Could not load corpus: %s", exc)
            return []

    def _save_corpus(self, records: List[dict]) -> None:
        self.corpus_path.parent.mkdir(parents=True, exist_ok=True)
        with self.corpus_path.open("w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)

    async def build_or_update_corpus(self, urls: Iterable[str], replace: bool = False) -> None:
        scraper = WebScraper()
        new_records = await scraper.scrape(urls)

        if replace or not self._fallback_corpus:
            merged = new_records
        else:
            # Merge on URL/id; update existing, add new
            by_id = {it["id"]: it for it in self._fallback_corpus}
            for rec in new_records:
                by_id[rec["id"]] = rec
            merged = list(by_id.values())

        self._save_corpus(merged)
        self._fallback_corpus = merged

    async def search(self, query: str, intent: Optional[str] = None) -> List[Citation]:
        """
        Very simple keyword search over title/description/tags/text.
        You can swap this for TF-IDF or BM25 later.
        """
        if not self._fallback_corpus:
            LOGGER.info("No corpus available; nothing to search.")
            return []

        q = query.lower()
        tokens = [t for t in re.split(r"\W+", q) if t]
        if not tokens:
            return []

        scored: List[tuple[float, dict]] = []
        for item in self._fallback_corpus:
            blob = " ".join([
                str(item.get("title", "")),
                str(item.get("description", "")),
                " ".join(item.get("tags", [])),
                str(item.get("text", "")),
            ]).lower()

            # crude scoring: count token hits; small bonus if intent is in tags
            score = sum(blob.count(tok) for tok in tokens)
            if intent and intent in item.get("tags", []):
                score += 2

            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = [self._citation_from_item(it, source="Scraped Corpus") for _, it in scored[:3]]
        return top

    @staticmethod
    def _citation_from_item(item: dict, source: str) -> Citation:
        return Citation(
            id=str(item.get("id", item.get("url", "scraped"))),
            title=item.get("title", "Web Resource"),
            url=item.get("url", ""),
            source=source,
            snippet=item.get("description", ""),
            retrieved=item.get("retrieved"),
        )


# ---------------------------------------------------------------------
# Example usage (run as a script)
# ---------------------------------------------------------------------
if __name__ == "__main__":
    async def main():
        svc = SearchService()
        # 1) Build/refresh corpus from a starter set of pages
        seed_urls = [
    "https://www.njit.edu/",
    "https://njit.campuslabs.com/engage/events",
    "https://www.njit.edu/financialaid/merit-based-scholarships",
    "https://www.njit.edu/financialaid/scholarship-universe-njit",
    "https://www.njit.edu/research/",
    "https://research.njit.edu/bioscience-and-bioengineering",
    "https://research.njit.edu/data-science-and-management",
    "https://research.njit.edu/environment-and-sustainability",
    "https://research.njit.edu/robotics-and-machine-intelligence",
    "https://research.njit.edu/uri/",
    "https://www.njit.edu/counseling/services",
    "https://www.njit.edu/counseling/mantra-health-mental-health-wellness",
    "https://www.njit.edu/counseling/uwill-mental-health-and-wellness-service",
    "https://app.uwill.com/login",
    "https://hub.mantrahealth.com/login?utm_content=70&utm_source=schoolsitereferral&utm_medium=digital&utm_campaign=schoolsitereferral&to=%2F%3Futm_content%3D70%26utm_source%3Dschoolsitereferral%26utm_medium%3Ddigital%26utm_campaign%3Dschoolsitereferral",
    "https://www.njit.edu/tlc/facilities",
    "https://www.njit.edu/tlc/",
            
           
        ]
        await svc.build_or_update_corpus(seed_urls, replace=False)

        # 2) Search it
        results = await svc.search("research opportunities and events", intent="events")
        for c in results:
            print(f"- {c.title} [{c.url}] :: {c.snippet[:120]}...")

    asyncio.run(main())

# put this anywhere (e.g., below SearchService definition) and run it once
async def add_manual_resources(manual: List[Dict[str, Any]], corpus_path: str = "data-ingestion/njit_resources.json"):
    svc = SearchService(Path(corpus_path))
    # load existing corpus
    corpus = svc._load_corpus()

    # merge by id (same logic as build_or_update_corpus)
    by_id = {it["id"]: it for it in corpus}
    for rec in manual:
        by_id[rec["id"]] = rec

    merged = list(by_id.values())
    svc._save_corpus(merged)


asyncio.run(add_manual_resources([
  {
    "id": "https://www.khanacademy.org/",
    "title": "Khan Academy",
    "url": "https://www.khanacademy.org/",
    "source": "Khan Academy",
    "description": "Free online courses, lessons, and practice in math, science, computing, economics, and more.",
    "retrieved": None,
    "tags": ["academic help", "academic", "knowledge"],
    "text": "Educational videos and exercises across math, physics, chemistry, computer science, finance, and test prep."
  },
  {
    "id": "https://www.geeksforgeeks.org/",
    "title": "GeeksforGeeks",
    "url": "https://www.geeksforgeeks.org/",
    "source": "GeeksforGeeks",
    "description": "Computer science portal with tutorials, coding problems, interview preparation, and courses.",
    "retrieved": None,
    "tags": ["academic help", "coding", "knowledge", "career"],
    "text": "Articles, coding practice, and learning resources for programming, data structures, algorithms, and technical interview prep."
  },
  {
    "id": "https://www.youtube.com/@alexlorenlee",
    "title": "Alex Lorén Lee",
    "url": "https://www.youtube.com/@alexlorenlee",
    "source": "YouTube",
    "description": "Math educator sharing clear explanations and problem-solving strategies.",
    "retrieved": None,
    "tags": ["academic help", "math", "knowledge"],
    "text": "YouTube channel focused on mathematics with intuitive explanations and detailed walkthroughs of problem-solving methods."
  },
  {
    "id": "https://www.youtube.com/@PhysicsNinja",
    "title": "Physics Ninja",
    "url": "https://www.youtube.com/@PhysicsNinja",
    "source": "YouTube",
    "description": "Physics tutorials covering mechanics, electromagnetism, and exam preparation.",
    "retrieved": None,
    "tags": ["academic help", "physics", "knowledge"],
    "text": "YouTube channel with physics lectures, examples, and problem solving aimed at helping students succeed in physics courses."
  }
]))
