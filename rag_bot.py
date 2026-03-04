import logging
import sys

from google import genai
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from supabase import Client, create_client

from src.config import (
    AI_MODEL,
    GOOGLE_API_KEY,
    SLACK_APP_TOKEN,
    SLACK_BOT_TOKEN,
    SUPABASE_KEY,
    SUPABASE_URL,
)

# ロギング設定
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# 1. 初期化チェック
if not all([GOOGLE_API_KEY, SUPABASE_URL, SUPABASE_KEY, SLACK_BOT_TOKEN, SLACK_APP_TOKEN]):
    logger.error("❌ 必要な環境変数が設定されていません (.env または Railwayの変設定を確認してください)")
    sys.exit(1)

# 各クライアントのセットアップ
try:
    genai_client = genai.Client(api_key=GOOGLE_API_KEY)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Slack Boltアプリの初期化
    app = App(token=SLACK_BOT_TOKEN)
except Exception as e:
    logger.error(f"❌ クライアントの初期化に失敗しました: {e}")
    sys.exit(1)


# 2. メンションを受け取った時の処理
@app.event("app_mention")
def handle_mention(event, say):
    # メンション部分 (<@U123456>) を除去してクエリを抽出
    text = event.get("text", "")
    if ">" in text:
        user_query = text.split(">")[-1].strip()
    else:
        user_query = text.strip()

    logger.info(f"📩 質問を受け取りました: {user_query}")

    if not user_query:
        say("質問内容が読み取れませんでした。")
        return

    # 処理中であることをリアクションで伝える
    try:
        app.client.reactions_add(channel=event["channel"], name="eyes", timestamp=event["ts"])
    except Exception as e:
        logger.warning(f"リアクションの追加に失敗しました: {e}")

    # ⏳ 処理中メッセージ用変数の初期化
    processing_msg_ts = None

    try:
        # 1. まず「考え中」メッセージを送る（これでユーザーは安心します）
        processing_msg = say(f"「{user_query}」について調べています... :thinking_face:")
        processing_msg_ts = processing_msg["ts"]

        # A. 質問をベクトル化（3072次元）
        # src/rag_indexer.py と同じモデルを使用
        query_res = genai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=user_query,
            config={"task_type": "RETRIEVAL_QUERY"},
        )
        query_vector = query_res.embeddings[0].values

        # B. Supabaseで似ている記事を検索（SQLで作った関数を呼び出す）
        matched_docs = supabase.rpc(
            "match_articles",
            {
                "query_embedding": query_vector,
                "match_threshold": 0.3,  # 類似度のしきい値
                "match_count": 3,  # 上位3件を取得
            },
        ).execute()

        # C. 検索結果をコンテキストとして整形
        if not matched_docs.data:
            app.client.chat_update(
                channel=event["channel"],
                ts=processing_msg_ts,
                text=f"申し訳ありません。「{user_query}」に関連する記事が見つかりませんでした。",
            )
            return

        context_text = ""
        for d in matched_docs.data:
            context_text += f"\n■ {d.get('title')}\n{d.get('content', '')[:500]}...\n(URL: {d.get('url')})\n"

        # D. Geminiに「記事の内容に基づいて」回答させる
        prompt = f"""
        あなたは多忙なエンジニアのための技術情報アシスタントです。
        以下の【参考記事】から、ユーザーの質問に関連する記事（最大3件）を選び、それぞれの「おすすめポイント」を簡潔に伝えてください。

        【ルール】
        ・挨拶や長い説明は省略し、結果だけを返してください。
        ・各記事につき、おすすめポイントは1〜2文で短くまとめてください。
        ・記事タイトルは必ず `*記事タイトル*` のようにアスタリスクで囲んでください。
        ・以下の【出力フォーマット例】に厳密に従ってください。

        【出力フォーマット例】
        *記事タイトル1*
        ・おすすめポイントをここに記述します。

        *記事タイトル2*
        ・おすすめポイントをここに記述します。

        【参考記事】:
        {context_text}

        【ユーザーの質問】:
        {user_query}
        """

        response = genai_client.models.generate_content(model=AI_MODEL, contents=prompt)
        answer_text = response.text

        # E. Slackに回答を投稿
        # 参照した記事のリストを作成
        sources_mrkdwn = "\n".join([f"• <{d.get('url')}|{d.get('title')}>" for d in matched_docs.data])

        blocks = [
            {"type": "section", "text": {"type": "mrkdwn", "text": answer_text}},
            {"type": "divider"},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"📚 *参照記事*\n{sources_mrkdwn}"}],
            },
        ]

        # text引数はプッシュ通知などで使われるプレーンテキスト
        # say() ではなく chat_update() で「考え中」メッセージを上書きする
        app.client.chat_update(
            channel=event["channel"],
            ts=processing_msg_ts,
            blocks=blocks,
            text=f"「{user_query}」についての回答です。",
        )

    except Exception as e:
        logger.error(f"Error in handle_mention: {e}")
        if processing_msg_ts:
            try:
                app.client.chat_update(
                    channel=event["channel"],
                    ts=processing_msg_ts,
                    text="エラーが発生しました。時間を置いて再度お試しください。",
                )
            except Exception as e_say:
                logger.error(f"Failed to send error message to Slack: {e_say}")


# 3. ボットの起動
if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    logger.info("⚡️ Slack RAG Bot is running!")
    handler.start()
