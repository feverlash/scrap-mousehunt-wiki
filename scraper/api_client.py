import time
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from typing import List, Dict, Any, Optional

from scraper.config import API_URL, USER_AGENT, DEFAULT_DELAY

class WikiClient:
    """Client for querying the MouseHunt MediaWiki API with retries and rate limiting."""

    def __init__(self, delay: float = DEFAULT_DELAY):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

        # Configure resilient retry strategy
        retries = Retry(
            total=5,
            backoff_factor=1.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_category_members(self, category_name: str, cmtype: str = "page", limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Fetch all page members of a given category with pagination.
        
        Args:
            category_name: e.g. "Weapons" or "Mice"
            cmtype: 'page', 'subcat', or 'file'
            limit: optional maximum number of items to retrieve
        """
        cmtitle = f"Category:{category_name}" if not category_name.startswith("Category:") else category_name
        members = []
        cmcontinue = None

        while True:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": cmtitle,
                "cmtype": cmtype,
                "cmlimit": 500,
                "format": "json"
            }
            if cmcontinue:
                params["cmcontinue"] = cmcontinue

            try:
                resp = self.session.get(API_URL, params=params, timeout=20)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[Error] Failed to fetch category {cmtitle}: {e}")
                break

            batch = data.get("query", {}).get("categorymembers", [])
            for item in batch:
                members.append(item)
                if limit is not None and len(members) >= limit:
                    return members

            if "continue" in data and (limit is None or len(members) < limit):
                cmcontinue = data["continue"].get("cmcontinue")
                time.sleep(self.delay)
            else:
                break

        return members

    def get_page_data(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Parse a page by title, following redirects and extracting HTML text and categories.
        """
        params = {
            "action": "parse",
            "page": title,
            "prop": "text|categories|sections",
            "redirects": "1",
            "format": "json"
        }
        try:
            resp = self.session.get(API_URL, params=params, timeout=25)
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                print(f"[Warning] API Error for page '{title}': {data['error'].get('info', '')}")
                return None
            return data.get("parse")
        except Exception as e:
            print(f"[Error] Failed to parse page '{title}': {e}")
            return None
        finally:
            time.sleep(self.delay)
