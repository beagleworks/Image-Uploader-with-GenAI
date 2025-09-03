# 画像アップローダー with AI画像生成

このアプリケーションは、画像をアップロードし、コメントを追加し、AI（Google Gemini 2.5 Flash Image）と連携して新しい画像を生成することができるシンプルなウェブアプリケーションです。

## 機能
- 画像アップロード（JPEG, PNG, GIF対応）
- コメント追加
- **コメント編集機能**（アップロード後のコメントを編集可能）
- **AI画像生成機能**（OpenRouterを介してGoogle Gemini 2.5 Flash Image (Nano Banana)を使用）
- 画像削除機能
- **データベースリセット機能**（すべてのデータを削除して初期状態に戻す）

## AI画像生成
アプリケーションの「🤖 AI」ボタンを使用すると、OpenRouterを介してGoogle Gemini 2.5 Flash Image (Nano Banana)がアップロードされた画像とコメントを基に、創造的な新しい画像を生成します。

**注意**: この機能にはOpenRouter APIキーと料金がかかります。生成された画像はローカルの `generated/` フォルダに保存されます。

## データベースリセット
アプリケーションのヘッダーにある「🔄 DBリセット」ボタンを使用すると、すべての画像データとデータベースを初期状態に戻すことができます。

**注意**: この操作は取り消すことができません。すべてのアップロードされた画像と生成されたAI画像が削除されます。

## 環境要件
- **OS**: Linux
- **Python**: 3.13.7 (mise経由で管理)
- **Webブラウザ**: 最新版（Chrome, Firefox, Safariなど）

## セットアップ
1. **Python環境の準備**:
   ```bash
   # miseを使用してPython 3.13.7をインストール（既にインストール済み）
   mise use python@3.13.7
   ```

2. **依存パッケージのインストール**:
   ```bash
   cd /home/beagleworks/AIPJ/pj2
   pip install -r requirements.txt
   ```

3. **OpenRouter APIキーの設定**:
   ```bash
   # .envファイルを編集してAPIキーを設定
   # OpenRouterからAPIキーを取得: https://openrouter.ai/keys
   echo "OPENROUTER_API_KEY=your_actual_api_key_here" > .env
   ```
   
   または、直接`.env`ファイルを編集してください。

4. **アプリケーションの実行**:
   ```bash
   python app.py
   ```

5. **ブラウザでアクセス**:
   - URL: http://127.0.0.1:5000
   - アプリケーションが起動すると自動的にブラウザで開きます

## プロジェクト構造
```
pj2/
├── app.py                 # Flaskバックエンドアプリケーション
├── requirements.txt       # Python依存関係
├── .env                  # 環境変数ファイル（APIキーなど）
├── database.db           # SQLiteデータベース（実行時に生成）
├── README.md             # このファイル
├── specs/
│   └── spec.md          # 詳細な仕様書
├── static/
│   ├── style.css        # CSSスタイルシート
│   └── script.js        # JavaScriptファイル
├── templates/
│   └── index.html       # HTMLテンプレート
├── uploads/             # アップロード画像保存ディレクトリ
└── generated/           # AI生成画像保存ディレクトリ
```

## 仕様書
詳細な仕様は `specs/spec.md` を参照してください。

## 技術スタック
- **バックエンド**: Python 3.13.7 + Flask 2.3.3
- **フロントエンド**: HTML5, CSS3, JavaScript (Vanilla JS)
- **AI**: Google Gemini 2.5 Flash Image (Nano Banana) via OpenRouter
- **データベース**: SQLite 3
- **画像処理**: Pillow 10.4.0
- **HTTPクライアント**: requests==2.31.0
- **環境管理**: mise + python-dotenv
- **バージョン管理**: Git

## 使用方法
1. **画像アップロード**:
   - 「画像を選択」ボタンで画像ファイルを選択
   - コメントを入力（任意）
   - 「🚀 アップロード」ボタンをクリック

2. **コメント編集**:
   - アップロードされた画像の「✏️ 編集」ボタンをクリック
   - コメントを編集して「保存」ボタンをクリック
   - 「キャンセル」ボタンで編集を中止

3. **画像削除**:
   - 各画像の「削除」ボタンをクリック
   - 確認ダイアログで「OK」を選択

4. **データベースリセット**:
   - ヘッダーの「🔄 DBリセット」ボタンをクリック
   - 二重確認ダイアログで「OK」を選択

## 注意事項
- **OpenRouter API**: 使用にはAPIキーと料金がかかります
- **画像保存**: アップロードされた画像はローカルの `uploads/` フォルダに保存されます
- **生成画像**: AI生成された画像はローカルの `generated/` フォルダに保存されます
- **データベース**: SQLiteファイルは `database.db` として保存されます
- **開発環境**: このアプリケーションは開発環境専用です
- **セキュリティ**: アップロードファイルのサイズ制限（16MB）とタイプ検証を実装しています

## トラブルシューティング
- **画像が表示されない**: ブラウザのキャッシュをクリアするか、URLエンコードの問題を確認
- **APIエラー**: OpenRouter APIキーが正しく設定されているか確認
- **生成エラー**: 画像ファイルが破損していないか、サポートされている形式か確認
- **データベースエラー**: `database.db` ファイルの権限を確認、またはDBリセット機能を使用

## 開発情報
- **コミット**: `bd684c6`
- **最終更新**: 2025年9月2日
- **開発環境**: Linux + mise + Python 3.13.7
