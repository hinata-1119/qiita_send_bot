import json
import logging

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from src.config import (
    GOOGLE_CREDENTIALS_JSON,
    IS_GITHUB_ACTIONS,
    SPREADSHEET_KEY,
    STORAGE_FILE_PATH,
)

logger = logging.getLogger(__name__)


def _get_worksheet():
    # デバッグ情報を出力（Secretsの中身を直接出さないよう文字数だけ確認）
    logger.info(
        f"DEBUG: GOOGLE_CREDENTIALS_JSON exists: {bool(GOOGLE_CREDENTIALS_JSON)}"
    )
    if GOOGLE_CREDENTIALS_JSON:
        logger.info(f"DEBUG: JSON Length: {len(GOOGLE_CREDENTIALS_JSON)}")
        logger.info(
            f"DEBUG: First 5 chars: {GOOGLE_CREDENTIALS_JSON[:5]}"
        )  # '{' から始まっているか確認

    if not GOOGLE_CREDENTIALS_JSON or not SPREADSHEET_KEY:
        logger.error("Credentials or Spreadsheet Key is missing.")
        return None

    try:
        creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON.strip())
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_KEY).sheet1
    except Exception as e:
        logger.error(f"Spreadsheet connection failed: {e}")
        return None


def load_notified_ids() -> set:
    if IS_GITHUB_ACTIONS:
        # 本番：スプレッドシートから読み込み
        worksheet = _get_worksheet()
        if not worksheet:
            return set()
        try:
            records = worksheet.col_values(1)
            return set(line.strip() for line in records if line.strip())
        except Exception as e:
            logger.error(f"Failed to load notified IDs from Sheets: {e}")
            return set()
    else:
        # ローカル：テキストファイルから読み込み
        if not STORAGE_FILE_PATH.exists():
            return set()
        try:
            with open(STORAGE_FILE_PATH, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Failed to load notified IDs from local file: {e}")
            return set()


def save_notified_ids(new_ids: list):
    if not new_ids:
        return

    if IS_GITHUB_ACTIONS:
        # 本番：スプレッドシートに書き込み
        worksheet = _get_worksheet()
        if not worksheet:
            return
        try:
            rows = [[new_id] for new_id in new_ids]
            worksheet.append_rows(rows)
        except Exception as e:
            logger.error(f"Failed to save notified IDs to Sheets: {e}")
    else:
        # ローカル：テキストファイルに書き込み
        try:
            # dataフォルダが存在しない場合は自動作成
            STORAGE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(STORAGE_FILE_PATH, "a", encoding="utf-8") as f:
                for new_id in new_ids:
                    f.write(f"{new_id}\n")
        except Exception as e:
            logger.error(f"Failed to save notified IDs to local file: {e}")
