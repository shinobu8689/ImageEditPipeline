※日本語は英語の後にあります。／Japanese version below.

# ImageEditPipeline

In the world of disinformation by AI-generated imagery and non-legal uses of illustration, this tool helps content creators edit images and add watermarks in batch via a user-customisable workflow — now with a browser-based frontend.

---

## Libraries Used

- `rembg` — background removal via BiRefNet
- `Pillow` — core image processing
- `numpy` — noise generation
- `fastapi` / `uvicorn` — web server
- `python-multipart` — file upload support

---

## Setup

```bash
pip install -r requirements.txt
```

## Run (Web UI)

```bash
uvicorn server:app --reload
```

Then open **http://localhost:8000**

## Run (CLI / Batch)

```bash
python edit_pipeline.py
# Drag and drop a workflow .txt file when prompted
# Processes all images in ./img against that workflow
```

---

## Project Structure

```
ImageEditPipeline/
├── server.py           ← FastAPI backend (web UI)
├── edit_pipeline.py    ← CLI batch runner
├── img_obj.py          ← ImgX class, all image operations
├── static/
│   └── index.html      ← Single-page web frontend
├── img/                ← Input images (batch mode reads from here)
├── material/           ← Source assets / textures / watermarks
├── output/             ← Saved output images
├── Fonts/              ← Fonts used by the text command
└── requirements.txt
```

---

## Web UI Features

### Layer Panel — Stack Tab (left)
- Upload images via drag-and-drop or file picker — each pushed onto the layer stack
- Click any layer card to select it and preview it in the canvas
- Inline **Rename** and **Delete** per layer card
- Layer count shown in header

### Layer Panel — Files Tab (left)
- Browse `img/`, `material/`, and `output/` folders directly
- Thumbnail previews per file
- **+ Load** button pushes any file onto the layer stack
- Collapsible folder sections with a Refresh button

### Canvas (centre)
- Live preview of the selected layer
- **⟳ Refresh** — re-fetches all layers from server
- **↓ PNG / ↓ JPG** — downloads the currently selected layer

### Command Tab (right)
- Type any DSL command (e.g. `alph 0 0.5`) and hit Enter or ▶
- Full scrollable log with colour-coded output (✓ green, ✗ orange)
- Command always operates on the layer selected in the left panel

### Workflow Tab (right)
- Paste or type a multi-line DSL script
- **▶ Run Workflow** executes all lines in sequence
- **↑ Load .txt** — load a workflow file from disk
- Per-line log output shown below the editor

### Manual Tab (right)
- All operations act on whichever layer is selected in the left panel (shown in the badge at the top)
- GUI controls for every operation:
  - Opacity slider
  - Resize (exact px) / Rescale (× factor)
  - Crop — advanced (L/T/R/B), square
  - Rotate slider (−180° to 180°)
  - Noise (strength slider + type selector)
  - Move offset (px)
  - Fit mode with numpad position picker
  - Add text (x/y position, size slider)
  - Layer ops: Copy, Composite Down, Composite All, Delete, Move to index, Rename
  - Background removal (BiRefNet — slow on first run)

### Ref Tab (right)
- Clickable cheat-sheet of all DSL commands
- Click any entry to insert it into the command input

---

## Concepts

### Alignment / Angle (Numpad-style)

Whenever a command requires an alignment or position angle, it uses numpad-style positioning:

```
7 = top-left     8 = top-centre   9 = top-right
4 = mid-left     5 = centre       6 = mid-right
1 = bot-left     2 = bot-centre   3 = bot-right
```

### Layer vs Image

Commands ending in **`l`** (mostly) refer to **layer actions** — operations that affect the ordering or existence of layers in the stack.

Commands ending in **`x`** refer to **image actions** — operations on the image content within a layer, without affecting layer ordering.

- **Layer** — a slot in the stack; controls compositing order.
- **Image** — the pixel content belonging to a layer.

---

## Command Reference

### Setting Actions

| Command | Usage | Description |
|---------|-------|-------------|
| `scav` | `scav [int]` | Set the standard scaling value used by `fitx` |
| `step` | `step [bool]` | Toggle step-by-step layer display (CLI only) |
| `show` | `show` | One-off layer display at current step (CLI only) |
| `wait` | `wait` | Pause workflow until Enter is pressed (CLI only) |

### Layer Actions

| Command | Usage | Description |
|---------|-------|-------------|
| `load` | `load [path] [name]` | Load an image file onto a new layer |
| `copy` | `copy [layer] [name]` | Copy a layer's content to a new layer |
| `comd` | `comd [layer]` | Composite layer down onto the one below |
| `coma` | `coma` | Composite all layers down to layer 0 (flatten) |
| `newx` | `newx [name] [w] [h]` | Create a new blank (transparent) layer |
| `movl` | `movl [layer] [destination]` | Move a layer to a different stack position |
| `dell` | `dell [layer]` | Delete a layer |

### Image Actions

| Command | Usage | Description |
|---------|-------|-------------|
| `alph` | `alph [layer] [val]` | Set layer opacity (0.0 – 1.0) |
| `fitx` | `fitx [layer] [type] [angle]` | Fit image to canvas size |
| | `fitx L std angle` | Scale to base image height preserving aspect ratio, then pad |
| | `fitx L crop angle` | Scale to square based on height, pad, then crop |
| | `fitx L scale` | Scale based on base image height (no angle needed) |
| `rmbg` | `rmbg [layer]` | Remove background using BiRefNet |
| `save` | `save [layer]` | Save layer as JPG to `./output` (CLI only; use ↓ buttons in UI) |
| `croa` | `croa [layer] [left] [top] [right] [bottom]` | Crop to specified coordinates |
| `cros` | `cros [layer] [angle] [width] [height]` | Crop from a numpad-positioned corner, keeping given dimensions |
| `croq` | `croq [layer]` | Crop to square using the shortest side |
| `tile` | `tile [layer] [offset-bool] [w*] [h*]` | Tile image to fill a canvas; `*` optional (defaults to layer 0 size) |
| `resz` | `resz [layer] [w] [h]` | Resize image to exact pixel dimensions (not to scale) |
| `resl` | `resl [layer] [scale]` | Rescale image by a factor (e.g. `0.5`, `2.0`) |
| `nois` | `nois [layer] [strength] [type]` | Add noise; type: `gaussian` (default), `uniform`, `salt_pepper` |
| `movx` | `movx [layer] [x] [y]` | Shift image within its canvas (−x = left, +x = right, −y = up, +y = down) |
| `jitt` | `jitt [layer] [range]` | Randomly shift image within ±range pixels |
| `text` | `text [layer] [x] [y] [str] [size] [padding=bool] [font_path]` | Composite text onto the image |
| `rota` | `rota [layer] [degree]` | Rotate image (positive = clockwise) |

---

## Change Log

**05/6**
- Fixed Web UI layering issue

**03/6**
- Web UI frontend (FastAPI + single-page app)
- File browser for `img/`, `material/`, `output/` folders
- Manual edit panel with GUI controls for all operations
- Added `nois`, `movx`, `jitt`, `text`, `rota`

**30/5**
- Added process time result (CLI)
- Added `tile`
- Added `resz` / `resl`
- Added `wait`

**28/5**
- Added crop functions (`croa`, `cros`, `croq`)
- Added global setting commands (`scav`, `step`, `show`)
- Revised layer display command

**27/5**
- Initial git commit

**26/5**
- Modularised image editing into `ImgX` class in `img_obj.py`
- Separated layer actions and image actions
- Merged fit variants into single `fitx` command
- Implemented workflow engine

**25/5**
- Revival of old project



# ImageEditPipeline

AI生成画像による誤情報の拡散や、イラストの無断利用が増加する現代において、本ツールはコンテンツ制作者向けに、画像編集や透かし（ウォーターマーク）の追加をバッチ処理で行えるワークフロー型画像編集ツールです。

現在はブラウザベースのWebフロントエンドにも対応しています。

---

# 使用ライブラリ

* `rembg` — BiRefNetを利用した背景除去
* `Pillow` — 画像処理全般
* `numpy` — ノイズ生成
* `fastapi` / `uvicorn` — Webサーバー
* `python-multipart` — ファイルアップロード対応

---

# セットアップ

```bash
pip install -r requirements.txt
```

# 起動方法（Web UI）

```bash
uvicorn server:app --reload
```

起動後、以下へアクセスしてください。

```text
http://localhost:8000
```

---

# 起動方法（CLI / バッチ処理）

```bash
python edit_pipeline.py
```

起動後、ワークフロー定義用の `.txt` ファイルをドラッグ＆ドロップしてください。

`./img` フォルダ内のすべての画像に対して、指定したワークフローが実行されます。

---

# プロジェクト構成

```text
ImageEditPipeline/
├── server.py           ← FastAPIバックエンド（Web UI）
├── edit_pipeline.py    ← CLIバッチ実行
├── img_obj.py          ← ImgXクラス（画像編集機能）
├── static/
│   └── index.html      ← シングルページWebフロントエンド
├── img/                ← 入力画像
├── material/           ← 素材・テクスチャ・透かし画像
├── output/             ← 出力画像
├── Fonts/              ← textコマンド用フォント
└── requirements.txt
```

---

# Web UI 機能

## レイヤーパネル — Stack タブ（左側）

* ドラッグ＆ドロップまたはファイル選択で画像を追加
* 追加された画像はレイヤースタックへ登録
* レイヤーカードをクリックすると選択・プレビュー可能
* レイヤーごとの名前変更・削除
* 現在のレイヤー数を表示

---

## レイヤーパネル — Files タブ（左側）

* `img/`
* `material/`
* `output/`

各フォルダを直接参照可能

* サムネイル表示対応
* **+ Load** ボタンでレイヤーへ追加
* フォルダの折りたたみ対応
* Refreshボタンで再読込

---

## キャンバス（中央）

* 選択中レイヤーのリアルタイムプレビュー
* **⟳ Refresh**

  * サーバーから全レイヤーを再取得
* **↓ PNG / ↓ JPG**

  * 現在選択中のレイヤーを保存

---

## Command タブ（右側）

DSLコマンドを直接実行できます。

例：

```text
alph 0 0.5
```

* Enter または ▶ で実行
* カラー付きログ表示

  * ✓ 成功
  * ✗ エラー
* 選択中レイヤーに対して実行

---

## Workflow タブ（右側）

複数行のDSLスクリプトを実行できます。

* **▶ Run Workflow**

  * 上から順番に実行
* **↑ Load .txt**

  * ワークフローファイル読込
* 実行ログを表示

---

## Manual タブ（右側）

GUIから各種操作を実行できます。

### 画像編集

* 不透明度調整
* サイズ変更（px指定）
* 拡大縮小（倍率指定）
* トリミング

  * 詳細指定
  * 正方形切り抜き
* 回転（−180°〜180°）
* ノイズ追加
* 画像移動
* Fit配置
* テキスト追加

### レイヤー操作

* Copy
* Composite Down
* Composite All
* Delete
* Move
* Rename

### 背景除去

* BiRefNet利用
* 初回実行時は処理に時間がかかります

---

## Ref タブ（右側）

DSLコマンド一覧を表示

* 各項目をクリックすると入力欄へ挿入

---

# 基本概念

## 配置指定（テンキー方式）

位置や配置を指定するコマンドではテンキー形式を使用します。

```text
7 = 左上      8 = 上中央      9 = 右上
4 = 左中央    5 = 中央        6 = 右中央
1 = 左下      2 = 下中央      3 = 右下
```

---

## Layer と Image の違い

### Layer Action

主に `l` で終わるコマンド

レイヤーの順序や存在そのものを操作します。

### Image Action

主に `x` で終わるコマンド

画像内容のみを変更し、レイヤー順序には影響しません。

* **Layer**

  * スタック内のスロット
  * 合成順序を管理

* **Image**

  * レイヤー内の実際のピクセルデータ

---

# コマンド一覧

## 設定系

| コマンド   | 説明                 |
| ------ | ------------------ |
| `scav` | `fitx` の基準倍率を設定    |
| `step` | ステップごとの表示切替（CLIのみ） |
| `show` | 現在状態を表示（CLIのみ）     |
| `wait` | Enter入力まで停止（CLIのみ） |

---

## レイヤー操作

| コマンド   | 説明               |
| ------ | ---------------- |
| `load` | 画像を新規レイヤーとして読み込む |
| `copy` | レイヤー複製           |
| `comd` | 下レイヤーへ合成         |
| `coma` | 全レイヤーを統合         |
| `newx` | 空の透明レイヤー作成       |
| `movl` | レイヤー移動           |
| `dell` | レイヤー削除           |

---

## 画像操作

| コマンド   | 説明         |
| ------ | ---------- |
| `alph` | 不透明度変更     |
| `fitx` | キャンバスへフィット |
| `rmbg` | 背景除去       |
| `save` | JPG保存      |
| `croa` | 座標指定トリミング  |
| `cros` | 指定位置から切り抜き |
| `croq` | 正方形トリミング   |
| `tile` | タイル配置      |
| `resz` | ピクセル指定リサイズ |
| `resl` | 倍率指定リサイズ   |
| `nois` | ノイズ追加      |
| `movx` | 画像移動       |
| `jitt` | ランダム移動     |
| `text` | テキスト描画     |
| `rota` | 回転         |

---

# 更新履歴

### 2025/06/05

* Web UIのレイヤー表示問題を修正

### 2025/06/03

* FastAPIベースのWeb UIを追加
* `img` / `material` / `output` のファイルブラウザ追加
* GUI編集パネル追加
* `nois`
* `movx`
* `jitt`
* `text`
* `rota`
  を追加

### 2025/05/30

* 処理時間表示追加
* `tile` 追加
* `resz` / `resl` 追加
* `wait` 追加

### 2025/05/28

* トリミング機能追加

  * `croa`
  * `cros`
  * `croq`
* グローバル設定コマンド追加
* レイヤー表示コマンド改善

### 2025/05/27

* 初回Gitコミット

### 2025/05/26

* 画像編集機能を `ImgX` クラスへ整理
* レイヤー操作と画像操作を分離
* `fitx` に機能統合
* ワークフローエンジン実装

### 2025/05/25

* 旧プロジェクトを再始動
