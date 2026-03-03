import logging
import os

from google import genai
from supabase import Client, create_client

from src.config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# 環境変数の取得
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# 実行環境にキーが存在する場合のみ初期化（GitHub Actions等でのエラー防止）
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")


def save_article_to_supabase(title: str, url: str, content: str):
    """
    Qiitaの記事全文をGeminiでベクトル化し、Supabaseに保存する関数
    """
    if not supabase:
        logger.warning("Supabase client is not initialized. Skipping DB save.")
        return

    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY is missing. Skipping DB save.")
        return

    try:
        # APIの制限やエラーを防ぐため、念のため文字数を制限（例: 先頭10000文字）
        safe_content = content[:10000]

        client = genai.Client(api_key=GOOGLE_API_KEY)

        # 1. Geminiで全文をベクトル（埋め込み）に変換
        # 新しいSDK (google-genai) のメソッドを使用
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=safe_content,
            config={"task_type": "RETRIEVAL_DOCUMENT"},
        )
        # 新しいSDKのレスポンス構造に合わせて取得
        embedding = result.embeddings[0].values

        # 2. DBへ保存するデータ構造
        data = {"title": title, "url": url, "content": safe_content, "embedding": embedding}

        # 3. DBへUpsert（同じURLがあれば上書き、なければ新規追加）
        supabase.table("technical_articles").upsert(data, on_conflict="url").execute()
        logger.info(f"✅ DB saved: {title}")

    except Exception as e:
        logger.error(f"❌ DB save error ({title}): {e}")
