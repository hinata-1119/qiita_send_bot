import logging

from src.notified_ids import load_notified_ids, save_notified_ids
from src.qiita_client import fetch_qiita_articles
from src.slack_client import send_to_slack
from src.summarizer import summarize_article

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    logger.info("Service started.")

    articles = fetch_qiita_articles()
    if not articles:
        logger.info("No articles found.")
        return

    notified_ids = load_notified_ids()
    new_articles = [a for a in articles if a["id"] not in notified_ids]

    if not new_articles:
        logger.info("No new articles to notify.")
        return

    logger.info(f"Processing {len(new_articles)} new articles.")
    processed_ids = []

    for article in new_articles:
        logger.info(f"Analyzing: {article.get('title')}")
        summary = summarize_article(article)

        logger.info("Sending to Slack...")
        send_to_slack(article, summary)

        processed_ids.append(article["id"])

    if processed_ids:
        save_notified_ids(processed_ids)
        logger.info(f"History updated: {len(processed_ids)} items.")


if __name__ == "__main__":
    main()
