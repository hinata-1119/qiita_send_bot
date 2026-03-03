import logging

import google.api_core.exceptions
from google import genai

from src.config import AI_FALLBACK_MODEL, AI_MODEL, GOOGLE_API_KEY, USE_AI_SUMMARY
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
    content_to_analyze = f"【タイトル】\n{article.get('title', '')}\n\n【本文】\n{body_content}"

    # プロンプトと記事本文を結合
    full_prompt = f"{PROMPT}\n\n{content_to_analyze}"

    models_to_try = [AI_MODEL]
    if AI_FALLBACK_MODEL:
        models_to_try.append(AI_FALLBACK_MODEL)

    for model_name in models_to_try:
        try:
            logger.info(f"Attempting AI analysis with model: {model_name}")
            # 新しいSDKの生成メソッド
            response = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
            )
            return response.text
        except (
            google.api_core.exceptions.ServiceUnavailable,  # 503エラー (サーバー混雑)
            google.api_core.exceptions.ResourceExhausted,  # 429エラー (レート制限)
        ) as e:
            logger.warning(
                f"AI Analysis with model '{model_name}' failed due to a transient error: {e}. Trying next model."
            )
            # 一時的なエラーなので、次のフォールバックモデルを試す (ループは継続)
            pass
        except Exception as e:
            logger.error(f"AI Analysis with model '{model_name}' failed with a non-recoverable error: {e}")
            # APIキーの間違いやプロンプトの問題など、回復不能なエラーの場合はループを中断
            break

    logger.error(f"All AI models failed. Tried: {models_to_try}")
    return "⚠️ Summary generation failed."
