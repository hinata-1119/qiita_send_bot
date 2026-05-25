# Qiita Intelligence Monitor & RAG Bot

Google Gemini API を活用し、Qiita の注目記事を要約して Slack へ通知する「通知機能」と、蓄積した記事データに基づいて Slack 上の質問に自動応答する「RAG Bot機能」を併せ持つシステムです。

## 🎯 プロジェクトの目的
- **情報収集の効率化**: Qiita のトレンドや特定技術タグの記事を自動でフィルタリングし、AIによる要約をSlackにプッシュすることで、情報収集の時間を大幅に短縮します。
- **ナレッジの活用**: チームや個人で気になった記事をデータベースに蓄積し、必要な時にいつでも Slack から自然言語で対話的に検索・活用できる環境を構築します。

## ✨ 機能ハイライト

### 1. 通知サービス (`main.py`)
- **動的な監視対象**: `src/config.py` を編集するだけで、Qiita のトレンド全体、特定技術タグ、特定組織の投稿など、監視対象を柔軟に切り替えられます。
- **高品質なAI要約**: 構造化プロンプトにより、技術記事から「3行要約・背景・論点・結論・推奨読者」といった要点を的確に抽出します。
- **モバイルフレンドリー通知**: Slack Block Kit を活用し、スマートフォンでも見やすいレイアウトで通知します。
- **ハイブリッドな実行履歴管理**:
    - **本番 (GitHub Actions)**: Google Sheets API 経由でスプレッドシートに通知済みIDを記録。
    - **ローカル**: `data/notified_ids.txt` にIDを記録し、本番環境に影響を与えずにテスト可能。

### 2. RAG Bot サービス (`rag_bot.py`)
- **Slack との対話**: Slack で Bot にメンションするだけで、過去に通知した記事の中から関連性の高い情報を探し出し、質問に回答します。
- **ベクトル検索**: 記事の内容を `gemini-embedding-001` でベクトル化し、Supabase (PostgreSQL + pgvector) に保存。ユーザーの質問との意味的な類似度で記事を検索します。
- **文脈に基づいた回答生成**: 検索した記事の内容をコンテキストとして最新の Gemini モデルに与え、自然で的確な回答を生成します。

## 🛠️ システム構成
このプロジェクトは、目的の異なる2つの独立したサービスで構成されています。

1.  **通知サービス (バッチ処理)**
    - **実行環境**: GitHub Actions (スケジュール実行) / ローカルマシン
    - **メインスクリプト**: `main.py`
    - **役割**: Qiita 記事の取得、要約、Slack通知、Supabaseへの記事登録

2.  **RAG Bot (常駐プロセス)**
    - **実行環境**: Railway, Heroku 等のPaaS (Procfile にて定義)
    - **メインスクリプト**: `rag_bot.py`
    - **役割**: Slack からのメンションに応答し、Supabase内の記事を検索して回答を生成

### 共通技術スタック
- **Language**: Python 3.12+
- **Package Manager**: [uv](https://github.com/astral-sh/uv)
- **Linter / Formatter**: [Ruff](https://github.com/astral-sh/ruff)
- **Git Hooks**: pre-commit (Ruff, Gitleaks)
- **Database**: Supabase (PostgreSQL + pgvector)
- **Core Libraries**:
    - `google-genai`: Google Gemini API (要約・埋め込み・回答生成)
    - `slack-bolt`: Slack Bot フレームワーク (RAG Bot の対話処理)
    - `requests`: Qiita API, Slack Incoming Webhook
    - `gspread`, `oauth2client`: Google Sheets API
    - `supabase`: Supabase Python Client

### 📂 ディレクトリ構成
```text
.
├── .github/workflows/notify.yml   # 1. 通知サービス (GitHub Actions)
├── data/notified_ids.txt          # (ローカル実行時) 通知済みIDの保存先
├── src/
│   ├── config.py                  # 全体設定 (検索条件・APIキー・定数)
│   ├── notified_ids.py            # 通知済みIDの管理 (Local/Sheets)
│   ├── prompt.py                  # AI要約用プロンプト
│   ├── qiita_client.py            # Qiita API 連携
│   ├── rag_indexer.py             # 記事のベクトル化・Supabase保存
│   ├── slack_client.py            # Slack通知送信
│   └── summarizer.py              # Gemini APIでの要約処理
├── main.py                        # 1. 通知サービスの実行ファイル
├── rag_bot.py                     # 2. RAG Bot の実行ファイル
├── Procfile                       # 2. RAG Bot のPaaS用プロセス定義
├── schema.sql                     # SupabaseのDBテーブル・関数定義
├── .env.sample                    # 環境変数テンプレート
├── pyproject.toml                 # 依存関係定義 (uv)
├── README.md
└── uv.lock                        # 依存パッケージのロックファイル
```

## 🔑 環境変数
プロジェクト直下に `.env` ファイルを作成するか、実行環境の環境変数として設定してください。

| 変数名 | 内容 | 通知 | RAG | 備考 |
| :--- | :--- | :---: | :---: | :--- |
| `QIITA_TOKEN` | Qiita API 個人用アクセストークン | ✅ | - | [Qiita設定](https://qiita.com/settings/applications)から取得 |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | ✅ | - | 通知サービスからの投稿用 |
| `GOOGLE_API_KEY` | Google AI Studio API Key | ✅ | ✅ | Gemini API用 |
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token | - | ✅ | RAG Bot の対話機能用 (`xoxb-...`) |
| `SLACK_APP_TOKEN` | Slack App-Level Token | - | ✅ | Socket Mode 接続用 (`xapp-...`) |
| `SUPABASE_URL` | Supabase プロジェクト URL | ✅ | ✅ | RAGのデータストア |
| `SUPABASE_KEY` | Supabase API Key (anon推奨) | ✅ | ✅ | |
| `GOOGLE_CREDENTIALS_JSON` | GCPサービスアカウント認証JSON | (✅) | - | 本番(GHA)でのSheets連携時のみ |
| `SPREADSHEET_KEY` | 管理用スプレッドシートID | (✅) | - | 本番(GHA)でのSheets連携時のみ |


## 🚀 実行方法

### 1. 開発環境のセットアップ
```bash
# パッケージのインストールと仮想環境の同期
uv sync

# Gitフックを有効化 (コミット時の自動整形・シークレットチェック)
uv run pre-commit install
```

### 2. 通知サービスの実行 (ローカル)
ローカルファイル (`data/notified_ids.txt`) を使用して実行されます。`.env` に必要な変数を設定してください。

```bash
# スクリプトの実行
uv run main.py
```

### 3. RAG Bot の実行 (ローカル)
Socket Mode を使用してローカルマシンから Slack API に接続します。`.env` に必要な変数を設定してください。

```bash
# Botを起動
uv run rag_bot.py
```

### 4. 本番環境へのデプロイ

- **通知サービス**: `.github/workflows/notify.yml` により、リポジトリの Secrets を使って毎日定時実行されます。手動実行も可能です。
- **RAG Bot**: `Procfile` をサポートするPaaS（Railway, Herokuなど）にデプロイします。リポジトリの環境変数設定に `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` などを登録してください。

## 🔧 カスタマイズ

### 監視対象の変更
`src/config.py` の `SEARCH_TYPE` を変更すると、検索条件やSlack上の表示が一括で切り替わります。
```python
# "manabi"     : 特定タグ（マナビDXクエスト等）の全件監視
# "all_trend"  : Qiita全体のトレンド（人気記事）監視
SEARCH_TYPE = "all_trend"
```
- **FETCH_MODE**: `"tag"`（タグベース）または `"organization"`（組織ベース）を選択可能。
- **FETCH_LIMIT**: 一度の実行で通知・インデックスする最大記事数。

### AIモデルの変更
`src/config.py` で、要約や回答生成に使うモデルを変更できます。最新の Gemini 2.x 系列をデフォルトとしています。
```python
AI_MODEL = "gemini-2.5-flash"        # メインモデル
AI_FALLBACK_MODEL = "gemini-2.5-flash-lite" # フォールバック
```

### DBスキーマ
RAG機能のバックエンドとして、Supabase (PostgreSQL) を使用します。`schema.sql` を Supabase の SQL Editor で実行して初期化してください。
- 埋め込みモデル: `gemini-embedding-001`
- 次数: **768**

## 🛠️ 開発ツール
- **Ruff**: 高速な Python リンター/フォーマッター。`pyproject.toml` でルールを設定しています。
- **Pre-commit**: コミット前に Ruff のチェックと [Gitleaks](https://github.com/gitleaks/gitleaks) によるシークレット漏洩チェックを自動実行します。

---
### 参考 / References
本プロジェクトの開発にあたり、以下の記事の構成・アイデアを参考にさせていただきました。
- [気になる記事を効率的に情報収集！～ 「Googleアラート⇒GAS⇒Dify要約⇒Slack」の実装～｜M_R_K_W](https://note.com/m_r_k_w/n/n26698cd1c4b4)
