import logging
from datetime import datetime, timedelta, timezone

import requests

from src.config import (
    FETCH_DAYS,
    FETCH_MODE,
    MIN_STOCKS,
    QIITA_TOKEN,
    TARGET_ORGANIZATION,
    WATCH_TAGS,
)

logger = logging.getLogger(__name__)


def fetch_qiita_articles() -> list:
    headers = {}
    if QIITA_TOKEN:
        headers["Authorization"] = f"Bearer {QIITA_TOKEN}"

    query_parts = []

    if FETCH_MODE == "organization" and TARGET_ORGANIZATION:
        query_parts.append(f"organization:{TARGET_ORGANIZATION}")
    elif WATCH_TAGS:
        tags_query = " OR ".join([f"tag:{t}" for t in WATCH_TAGS])
        query_parts.append(f"({tags_query})")

    if MIN_STOCKS > 0:
        query_parts.append(f"stocks:>={MIN_STOCKS}")

    if FETCH_DAYS > 0:
        target_date = datetime.now(timezone(timedelta(hours=9))) - timedelta(days=FETCH_DAYS)
        query_parts.append(f"created:>={target_date.strftime('%Y-%m-%d')}")

    query = " ".join(query_parts)
    logger.info(f"Qiita API Query: {query}")

    url = "https://qiita.com/api/v2/items"
    all_articles = []
    page = 1

    # 最大10ページ（1000件）まで取得して、取りこぼしを防ぐ
    while page <= 10:
        params = {"query": query, "page": page, "per_page": 100}
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            items = response.json()
            if not items:
                break
            all_articles.extend(items)
            if len(items) < 100:
                break
            page += 1
        except requests.exceptions.RequestException as e:
            logger.error(f"Qiita API request failed: {e}")
            break
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            break

    return all_articles
