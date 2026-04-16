# CinemaBoard

映画の上映スケジュールを表示するWebアプリケーション。

## 技術スタック

### バックエンド
- Python / FastAPI / Uvicorn
- SQLite + SQLAlchemy
- APScheduler (定期取得)

### フロントエンド
- Vue 3 (Composition API) + TypeScript
- Vite
- Vuetify 3
- Pinia + Axios
- Vue Router 4

## セットアップ

### バックエンド

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

環境変数 `FETCH_INTERVAL_MINUTES` でスケジュール取得間隔を変更可能（デフォルト: 5分）。

終了するには、ターミナルで `Ctrl + C` を押してください。Uvicorn が停止し、APScheduler の定期取得も自動的に終了します。

### フロントエンド

```bash
cd frontend
npm install
npm run dev
```

終了するには、ターミナルで `Ctrl + C` を押してください。Vite 開発サーバーが停止します。

開発時は `http://localhost:5173` でアクセス。API は Vite のプロキシ経由でバックエンド (`localhost:8000`) へ転送されます。

## 機能

- **映画館一覧画面** ? 映画館ボタンを押してスケジュール画面へ遷移
- **スケジュール画面**
    - カレンダーで日付選択 → OK で取得・表示
    - 更新ボタンで再取得
    - **作品別表示** ? 同作品 (IMAX / 字幕 / 吹替など) をグルーピング
    - **スクリーン別表示** ? テレビ欄風タイムライン表示
