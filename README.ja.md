# EREX

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

EREX は、セマンティック理解を中心にしたメール抽出プラットフォームです。構成可能な NLP パイプラインと埋め込みベクトルにより、PST/MSG/EML などのメールから構造化データを抽出します。

## 主な機能

- Sentence-Transformers によるセマンティック抽出
- 署名・免責文・装飾行の軽量ノイズ除去
- 複数案件メール向けのブロック分割
- 設定可能なキーワード抽出とルール分類
- 集計可視化と任意の LLM 技術インサイト
- FastAPI + React/Vite の分離構成

## クイックスタート

### 前提

- Docker / Docker Compose
- リポジトリ直下の `.env`（`.env.example` を参照）

### Docker 起動

```bash
cd infra
docker compose up --build
```

### アクセス

- Frontend: `http://localhost:8002`
- Backend: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`

## セマンティック処理の CPU/GPU 切替

`.env` で設定:

- `SEMANTIC_ACCELERATOR=cpu|gpu|auto`
- `SEMANTIC_DEVICE=`（任意、例: `cuda:0`）
- `SEMANTIC_MODEL_AUTO_UNLOAD=true|false`（アイドル時に GPU モデルを自動解放）
- `SEMANTIC_MODEL_IDLE_SECONDS=600`（アンロードまでのアイドル秒数）

GPU 確認:

```bash
cd infra
docker compose exec backend nvidia-smi
```

## 主要 API

- `GET /pipeline/config`
- `POST /pipeline/upload`
- `GET /pipeline/files`
- `DELETE /pipeline/files`
- `POST /pipeline/run`
- `POST /pipeline/run/start`
- `GET /pipeline/run/{job_id}/progress`
- `GET /pipeline/run/{job_id}/result`
- `POST /pipeline/history`
- `GET /pipeline/history`
- `GET /pipeline/history/{id}`
- `DELETE /pipeline/history/{id}`
- `POST /pipeline/tech-insight`

## 開発

### Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 設定ソース

パイプライン設定はデフォルトでファイル由来です。DB が利用可能な場合は `db`、不可時は `file` にフォールバックします。

## ディレクトリ構成

- `backend/app/services/` コアパイプライン
- `backend/config/` テンプレート・辞書・ルール
- `frontend/` Web UI
- `infra/` Docker 構成
- `docs/` ドキュメント

## ライセンス

`LICENSE.md` を参照してください。
