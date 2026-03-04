import logging

import requests

from src.config import SLACK_BOT_SETTINGS, SLACK_WEBHOOK_URL

logger = logging.getLogger(__name__)


def post_message(text: str):
    """Slackにシンプルなテキストメッセージを投稿する"""
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL is not set.")
        return

    payload = {
        "username": SLACK_BOT_SETTINGS.get("display_name", "Qiita Monitor"),
        "icon_emoji": SLACK_BOT_SETTINGS.get("icon_emoji", ":robot_face:"),
        "text": text,
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")


def send_to_slack(article: dict, summary: str):
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL is not set.")
        return

    user_id = article.get("user", {}).get("id", "Unknown")
    user_icon = article.get("user", {}).get("profile_image_url", "")
    likes = article.get("likes_count", 0)
    url = article.get("url", "")
    title = article.get("title", "No Title")

    # 日付の整形 (ISO 8601形式の先頭10文字 YYYY-MM-DD を取得)
    created_at = article.get("created_at", "")
    date_str = created_at[:10] if created_at else "Unknown"

    # タグの整形（最大5つまで表示）
    tags = [t.get("name", "") for t in article.get("tags", [])]
    tags_str = ", ".join(tags[:5]) if tags else "No Tags"

    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*<{url}|{title}>*"}},
        {
            "type": "context",
            "elements": [
                {"type": "image", "image_url": user_icon, "alt_text": user_id},
                {
                    "type": "mrkdwn",
                    "text": f"*{user_id}*  |  📅 {date_str}  |  🏷 {tags_str}  |  👍 {likes} LGTM",  # noqa: E051
                },
            ],
        },
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": summary}},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Qiitaで読む",
                        "emoji": True,
                    },
                    "url": url,
                    "style": "primary",
                }
            ],
        },
    ]

    payload = {
        "username": SLACK_BOT_SETTINGS.get("display_name", "Qiita Monitor"),
        "icon_emoji": SLACK_BOT_SETTINGS.get("icon_emoji", ":robot_face:"),
        "blocks": blocks,
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {e}")
