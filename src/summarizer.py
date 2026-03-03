import logging

import google.api_core.exceptions
import httpx
import requests
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
        except google.api_core.exceptions.GoogleAPIError as e:
            # Google API関連のエラーをキャッチし、エラーコードで一時的か判断
            # 503: Service Unavailable, 429: Resource Exhausted
            if e.code in [503, 429]:
                logger.warning(f"AI Analysis with model '{model_name}' failed transient error (code {e.code}): {e}")
                # 一時的なエラーなので、次のフォールバックモデルを試す (ループは継続)
                pass
            else:
                logger.error(f"AI Analysis with model '{model_name}' failed API error (code {e.code}): {e}")
                # 回復不能なエラーの場合はループを中断
                break
        except (requests.exceptions.HTTPError, httpx.HTTPStatusError) as e:
            # underlying HTTP library (requests or httpx) のエラーを直接捕捉
            status_code = e.response.status_code if hasattr(e, "response") and e.response else None
            if status_code in [503, 429]:
                logger.warning(
                    f"AI Analysis with model '{model_name}' failed transient HTTP error (code {status_code}): {e} "
                )
                pass  # 一時的なエラーなので、次のフォールバックモデルを試す (ループは継続)
            else:
                logger.error(
                    f"AI Analysis with model '{model_name}' failed with an HTTP error (code {status_code}): {e}"
                )
                break
        except Exception as e:
            logger.error(f"AI Analysis with model '{model_name}' failed with an unexpected error: {e}")
            break

    logger.error(f"All AI models failed. Tried: {models_to_try}")
    return "⚠️ Summary generation failed."
