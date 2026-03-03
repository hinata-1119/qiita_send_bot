# Qiita Intelligence Monitor

Google Gemini API を活用し、Qiita の特定技術タグおよびトレンド記事からメタ情報を抽出して Slack へ通知する自動化システム。

## ⚙️ 主な機能
* **動的ルーティング**: `src/config.py` の `SEARCH_TYPE` を切り替えるだけで、Qiitaの検索クエリ、取得件数、Slack Botの表示名・アイコンが連動して変化。
* **AI分析**: 構造化プロンプトにより、技術記事の「3行要約・背景・論点・結論・推奨読者」を抽出。LLM特有の不要な前置きを排除し、即座に要点のみを出力。
* **通知最適化**: Slack Block Kit を採用し、モバイル端末での視認性（トリアージ効率）を最大化。
* **ハイブリッド・ステート管理**:
    * **本番環境 (GitHub Actions)**: Google Sheets API を利用し、通知済み記事のIDをスプレッドシートに永続化。
    * **ローカル環境**: `data/notified_ids.txt` を自動生成してローカルで完結（本番環境を汚染せずにテスト可能）。
* **スケジュール実行**: GitHub Actions による定時実行（デフォルト:07:00 / 19:00 JST）。

## 🛠 システム構成
* **Language**: Python 3.12
* **Package Manager**: uv
* **Linter / Formatter**: Ruff
* **Git Hooks**: pre-commit (Ruff, Gitleaks)
* **Core APIs & Libraries**:
    * Google Gemini API (`google-genai` SDK)
    * Google Sheets API (`gspread`, `oauth2client`)
    * Qiita API v2 (`requests`)
    * Slack Incoming Webhook (`requests`)

### 📂 ディレクトリ構成

```text
.
├── .github/
│   └── workflows/
│       └── notify.yml        # GitHub Actions 定期実行ワークフロー定義
├── data/
│   └── notified_ids.txt      # (ローカル実行時) 通知済み記事IDの保存先
├── src/
│   ├── config.py             # 設定管理 (検索条件・APIキー・定数)
│   ├── notified_ids.py       # 通知済みIDの読み書きロジック (Local/Sheets)
│   ├── prompt.py             # AI要約用プロンプト定義
│   ├── qiita_client.py       # Qiita API 連携 (記事検索・取得)
│   ├── slack_client.py       # Slack API 連携 (通知送信)
│   └── summarizer.py         # Gemini API 連携 (要約生成)
├── .env                      # 環境変数 (APIキー等 / git管理外)
├── .gitignore                # Git除外設定
├── .pre-commit-config.yaml   # pre-commit フック設定 (Ruff, Gitleaks等)
├── .python-version           # Pythonバージョン指定
├── main.py                   # アプリケーションの実行ファイル
├── pyproject.toml            # プロジェクト設定・依存関係定義 (uv)
├── README.md                 # プロジェクトドキュメント
└── uv.lock                   # 依存パッケージのロックファイル
```

## 🔑 環境変数 (GitHub Secrets / .env)
システム実行には以下の変数を設定してください。ローカル実行時は `.env` に、本番環境時は GitHub Secrets に登録します。

| 変数名 | 内容 | ローカル実行時の必須要否 |
| :--- | :--- | :---: |
| `QIITA_TOKEN` | Qiita API 個人用アクセストークン | ✅ 必須 |
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL | ✅ 必須 |
| `GOOGLE_API_KEY` | Google AI Studio API Key | ✅ 必須 |
| `GOOGLE_CREDENTIALS_JSON` | GCP サービスアカウントの認証 JSON | ❌ 不要 (空でOK) |
| `SPREADSHEET_KEY` | 管理用スプレッドシートの ID | ❌ 不要 (空でOK) |

## 🚀 実行方法

### 1. ローカルでの実行 (テスト・開発用)
自動的にローカルストレージモード（`data/notified_ids.txt` を使用）で動作します。プロジェクト直下に `.env` を作成し、変数を設定した上で以下を実行してください。

```bash
# パッケージのインストールと仮想環境の同期
uv sync

# スクリプトの実行
uv run main.py
```

#### 開発用セットアップ (pre-commit)
コミット時に自動でコード整形とチェックを行うため、以下のコマンドでGitフックを有効化してください。
```bash
uv run pre-commit install
```
### 2. GitHub Actions での実行 (本番運用)
環境変数 `GITHUB_ACTIONS=true` が自動的に検知され、スプレッドシートでの履歴管理モードで動作します。

* **自動実行**: `.github/workflows/notify.yml` に基づき、毎日 07:00 / 19:00 JST にスケジュール実行。
* **手動実行**: GitHub リポジトリの `Actions` タブから `Qiita Monitor` ワークフローを選択し、`Run workflow` をクリック。

## 🔧 設定のカスタマイズ

監視対象や動作モードを変更する場合は、`src/config.py` 内の以下の変数を編集してください。

```python
# "manabi"     : 特定タグ（マナビDXクエスト等）の全件監視
# "all_trend"  : Qiita全体のトレンド（人気記事）監視
SEARCH_TYPE = "manabi"
```

上記を変更するだけで、内部の検索タグ、ストック数の閾値、検索対象期間、Slack上のアイコン設定などが一括で切り替わります。

### 詳細設定 (Organization検索など)
タグ検索だけでなく、特定のOrganizationの記事を取得することも可能です。`src/config.py` の以下の項目を編集してください。

```python
FETCH_MODE = "organization"   # デフォルトは "tag"
TARGET_ORGANIZATION = "MDXQ"  # 対象のOrganization ID
```

## 参考 / References
本プロジェクトの開発にあたり、以下の記事の構成・アイデアを参考にさせていただきました。

- [気になる記事を効率的に情報収集！～ 「Googleアラート⇒GAS⇒Dify要約⇒Slack」の実装～｜M_R_K_W](https://note.com/m_r_k_w/n/n26698cd1c4b4)
