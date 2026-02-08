# EREX

Language: [中文](README.md) | [English](README.en.md) | **日本語**

## 概要
EREX は、セマンティック理解を中心としたメール抽出プラットフォームです。  
Transformer Embedding を利用し、PST/MSG/EML などの大量メールに対して、意味的マッチング・ブロック分割・意図ベース抽出を行い、構造化データへ変換します。

### 主な機能
- Sentence-Transformers 類似度 + テンプレートによるセマンティック抽出
- 署名・免責文・装飾行などの軽量ノイズ除去
- `案件` / `案件名` などのマーカーでブロック分割
- 設定可能な辞書・ルールによるキーワード抽出 / 分類
- 集計・可視化、および OpenAI/LiteLLM 連携の技術インサイト
- FastAPI + React/Vite のフロント/バック分離構成

## クイックスタート（Docker）
### 1. 事前準備
- Docker / Docker Compose をインストール
- リポジトリ直下に `.env` を作成（`.env.example` を参照）
- 必要な設定を記入
  - `OPENAI_API_KEY`（tech insight 用・任意）
  - ポート / ログ / DB など

### 2. ビルドと起動
```bash
cd infra
docker compose up --build
```

### 2.1 セマンティック処理の CPU/GPU 切替
`.env` で設定:
- `SEMANTIC_ACCELERATOR=cpu|gpu|auto`
- `SEMANTIC_DEVICE=`（任意、例: `cuda:0`）

GPU 確認:
```bash
cd infra
docker compose exec backend nvidia-smi
```

### 3. アクセス
- Frontend: `http://localhost:8002`
- Backend API: `http://localhost:8000`（OpenAPI は `/docs`）

## 主要 API
- `GET /pipeline/config` - 現在の実行設定
- `POST /pipeline/upload` / `GET /pipeline/files` / `DELETE /pipeline/files` - ファイル管理
- `POST /pipeline/run` - パイプライン実行
- `POST /pipeline/run/start` + 進捗/結果 API - 非同期実行
- `POST /pipeline/history` 系 API - 実行履歴の保存/管理
- `POST /pipeline/tech-insight` - LLM によるキーワード説明

## 開発
- Backend: `cd backend && uv run uvicorn app.main:app --reload --port 8000`
- Frontend: `cd frontend && npm install && npm run dev`

## 設定ソース（DB / ファイル）
パイプライン設定は初期状態ではファイル読み込みです。  
DB が利用可能な場合、フロント保存時に DB へ反映され、`source=db` になります。利用不可時は `source=file` にフォールバックします。

## 主要ディレクトリ
- `backend/app/services/` - コア処理モジュール
- `backend/config/` - テンプレート・辞書・各種ルール
- `frontend/` - React フロントエンド
- `infra/` - Docker Compose / インフラ設定
