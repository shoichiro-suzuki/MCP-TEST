# ═══════════════════════════════════════════════════
# 言語設定 / Language Configuration
# ═══════════════════════════════════════════════════

**常に日本語で応答すること。**

例外: コード（変数名、関数名）、ファイルパス、URL、技術仕様の固有名詞

# ═══════════════════════════════════════════════════
# ドキュメント簡潔性ルール / Documentation Conciseness Rule
# ═══════════════════════════════════════════════════

**重要**: 以下を簡潔に記述すること。
- AGENTS.md
- docs/配下の全ドキュメント
- **Codexが生成する全ドキュメント**（コミットメッセージ、説明文、応答メッセージ等）

## 原則
- **重要な情報を濃縮**: 冗長な説明や当たり前の内容を避ける
- **おせっかいな説明を排除**: 経験豊富な開発者が読むことを前提とする
- **箇条書き優先**: 長文の説明文は避け、要点を箇条書きにする
- **具体例は最小限**: 本当に必要な例のみ記載

## 適用範囲

### 1. 静的ドキュメント
- AGENTS.md
- docs/配下のすべてのmdファイル

### 2. Codexが生成するドキュメント
- **コミットメッセージ**: 簡潔な1行要約 + 必要最小限の詳細
- **応答メッセージ**: 冗長な前置き・後置きを避ける
- **コード説明**: 必要最小限の情報のみ
- **PR説明**: 変更内容の要点のみ

## 例

### 応答メッセージ
❌ 冗長: "了解しました。それでは、まず関連するドキュメントを確認させていただき、その後実装に取り掛かります。実装が完了しましたら、ドキュメントも合わせて更新いたします。"
✅ 簡潔: "関連ドキュメント確認後、実装とドキュメント更新を行います。"

### コミットメッセージ
❌ 冗長: "feat: HybridRetrieverクラスを別ファイルに分離しました。これにより、将来的に他のツールと入れ替えることが可能になります。"
✅ 簡潔: "feat: HybridRetrieverを別ファイルに分離"

# ═══════════════════════════════════════════════════
# ドキュメント管理 / Documentation Management
# ═══════════════════════════════════════════════════

**CRITICAL: タスク実行時は必ず関連ドキュメントを同時更新すること。**

詳細は [docs/DOCUMENT_MANAGEMENT.md](docs/DOCUMENT_MANAGEMENT.md) を参照。

- ドキュメント一覧
- 更新義務（実装前後の参照・更新）
- 参照・更新マトリクス
- 品質基準

# ═══════════════════════════════════════════════════
# コード生成ルール / Code Generation Rules
# ═══════════════════════════════════════════════════

## 依存関係管理

**CRITICAL: グローバル環境へのpip install禁止**

- **禁止**: `pip install` をグローバル環境で実行
- **必須**: 仮想環境（`.venv`）を使用
- **例外**: なし

### 正しい手順
```bash
# 1. 仮想環境作成（初回のみ）
python -m venv .venv

# 2. 仮想環境有効化
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

# 3. 依存関係インストール
pip install -r requirements.txt
```

### テスト・実行時の注意

**CRITICAL: すべてのpython/pipコマンドは仮想環境内で実行**

```bash
# ✅ 正しい例
(.venv) $ python -m demo_app.services.llm_service
(.venv) $ pip install jsonschema

# ❌ 間違った例（仮想環境未有効化）
$ python -m demo_app.services.llm_service
$ pip install jsonschema
```

## 絵文字使用制限

- **禁止**: print()、logging、文字列リテラル
- **許可**: コメント内のみ

```python
# ❌ 禁止
print("処理完了✅")
logging.info("検索中...🔍")

# ✅ 推奨
print("処理完了")
logging.info("検索中...")
```

## 既存モジュール優先ルール

**Azure関連機能は既存モジュールを優先利用すること。**

### 既存Azureモジュール

- **`azure_/blob_storage.py`**
  - `AzureBlobStorageService` クラス
  - 主要メソッド: `get_sas_token()`, `list_blobs_with_prefix()`, `upload_blob()`
  - 用途: Blobストレージ操作、SAS URL生成

- **`azure_/openai_service.py`**
  - `AzureOpenAIService` クラス
  - 主要メソッド: `get_openai_response()` (テキスト応答、Function Calling対応)
  - 用途: Azure OpenAI API呼び出し

### 実装方針

1. **既存クラスをimportして利用**
   ```python
   from azure_.blob_storage import AzureBlobStorageService
   from azure_.openai_service import AzureOpenAIService
   ```

2. **機能拡張が必要な場合**
   - オプション1: 既存クラスに新メソッド追加
   - オプション2: ラッパークラス作成（`demo_app/services/` 配下）

3. **新規実装は最小限**
   - 既存クラスで対応できない機能のみ
