import logging

from google import genai

from src.config import AI_MODEL, GOOGLE_API_KEY, USE_AI_SUMMARY
from src.prompt import PROMPT

logger = logging.getLogger(__name__)


def summarize_article(article: dict) -> str:
    if not USE_AI_SUMMARY:
        return "（AI要約は無効化されています）"

    if not GOOGLE_API_KEY:
        logger.error("GOOGLE_API_KEY is missing.")
        return "Error: AI API Key not configured."

    # 新しいSDKのクライアント初期化
    client = genai.Client(api_key=GOOGLE_API_KEY)

    body_content = article.get("body", "")[:10000]
    content_to_analyze = (
        f"【タイトル】\n{article.get('title', '')}\n\n【本文】\n{body_content}"
    )

    # プロンプトと記事本文を結合
    full_prompt = f"{PROMPT}\n\n{content_to_analyze}"

    try:
        # 新しいSDKの生成メソッド
        response = client.models.generate_content(
            model=AI_MODEL,
            contents=full_prompt,
        )
        return response.text
    except Exception as e:
        logger.error(f"AI Analysis failed ({AI_MODEL}): {e}")
        return "⚠️ Summary generation failed."
