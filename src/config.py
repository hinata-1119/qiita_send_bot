import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

# ==========================================
# 認証情報・APIキー
# ==========================================
QIITA_TOKEN = os.environ.get("QIITA_TOKEN")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# ==========================================
# 🚀 ユーザー設定：ここを切り替えるだけ！
# ==========================================
SEARCH_TYPE = "all_trend"

if SEARCH_TYPE == "manabi":
    WATCH_TAGS = ["マナビDXクエスト", "マナビDXQuest", "マナビDXQ"]
    MIN_STOCKS = 0
    FETCH_DAYS = 30
    SLACK_BOT_SETTINGS = {
        "display_name": "MDXQ-News-Monitor",
        "icon_emoji": ":newspaper:",
    }
elif SEARCH_TYPE == "all_trend":
    WATCH_TAGS = []
    MIN_STOCKS = 20
    FETCH_DAYS = 7
    SLACK_BOT_SETTINGS = {
        "display_name": "Qiita-Trend-Monitor",
        "icon_emoji": ":fire:",
    }

# ==========================================
# 共通設定・AI設定
# ==========================================
FETCH_MODE = "tag"  # "tag" (デフォルト) または "organization"
FETCH_LIMIT = 5  # 一度に取得する記事の最大数 (Qiita APIのper_pageパラメータ)
USE_AI_SUMMARY = True
AI_MODEL = "gemini-2.5-flash"  # より高速で安定したモデルをメインに
AI_FALLBACK_MODEL = "gemini-2.5-flash-lite"  # メインモデル失敗時の代替モデル

# --- オプション設定 (将来的な拡張用) ---
TARGET_ORGANIZATION = "MDXQ"  # FETCH_MODE = "organization" の時のみ使用

# ==========================================
# 実行環境の判定と履歴管理設定
# ==========================================
# GitHub Actions上での実行かどうかを自動判定
IS_GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"

# [本番環境用] スプレッドシート設定
GOOGLE_CREDENTIALS_JSON = os.environ.get("GOOGLE_CREDENTIALS_JSON")
SPREADSHEET_KEY = os.environ.get("SPREADSHEET_KEY")

# [ローカル環境用] テキストファイル保存パス
STORAGE_FILE_PATH = ROOT_DIR / "data" / "notified_ids.txt"
