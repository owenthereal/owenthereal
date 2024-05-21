import logging
from typing import Any, Dict, List
import pathlib
import feedparser
import requests
import re
from datetime import datetime

DEFAULT_N = 5
DEFAULT_DATE_FORMAT = "%Y-%m-%d"

root = pathlib.Path(__file__).parent.resolve()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_feed(url: str) -> List[Dict[str, str]]:
    """Fetches and parses the RSS feed from the given URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
        if not feed.entries:
            logging.error("Malformed feed: no entries found")
            return []
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the feed: {e}")
        return []
    except Exception as e:
        logging.error(f"Error processing the feed: {e}")
        return []

    return [
        {
            "title": entry.title,
            "url": entry.link,
            "date": get_entry_date(entry),
        }
        for entry in feed.entries[:DEFAULT_N]
    ]

def format_feed_entry(entry: Dict[str, str]) -> str:
    """Formats a feed entry as a markdown link."""
    title = entry.get("title", "No Title")
    link = entry.get("url", "")
    date = entry.get("date", "")

    return f"[{title}]({link})"

def get_entry_date(entry: Any, date_format: str = DEFAULT_DATE_FORMAT) -> str:
    """Extracts and formats the publication date from a feed entry."""
    if hasattr(entry, "published_parsed"):
        published_time = datetime(*entry.published_parsed[:6])
        return published_time.strftime(date_format)
    return ""

def replace_chunk(content: str, marker: str, chunk: str, inline: bool = False) -> str:
    """Replaces a chunk of text between specified markers in the content."""
    pattern = f"<!-- {marker} start -->.*<!-- {marker} end -->"
    r = re.compile(pattern, re.DOTALL)

    if not inline:
        chunk = f"\n{chunk}\n"

    return r.sub(f"<!-- {marker} start -->{chunk}<!-- {marker} end -->", content)

if __name__ == "__main__":
    readme = root / "README.md"
    url = "https://owenou.com/feed.xml"
    feeds = fetch_feed(url)
    feeds_md = "\n\n".join([format_feed_entry(feed) for feed in feeds])
    readme_contents = readme.read_text()
    rewritten = replace_chunk(readme_contents, "blog", feeds_md)
    readme.write_text(rewritten)
    print(feeds_md)
