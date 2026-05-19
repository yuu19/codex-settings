# 読みやすい技術記事の執筆パターン

Zenn 記事「書籍『GitHub CI/CD実践ガイド』を読みやすくする技術」を参考に、技術記事へ適用しやすい形へ要約したルール。

## 基本方針

- シンプルにする。文章、コード、図表から余計な複雑さを取り除く。
- ノイズを減らす。読者が判断に迷う表現や視覚要素を削る。
- テンポを重視する。読者が前後を行き来しなくても読み進められる構成にする。

## 文章

- 一文を短くする。読点が複数必要になる文は分割か言い換えを検討する。
- 一文の中で同じ助詞、特に「の」「を」を繰り返さない。
- 曖昧な表現、口語、主語が追いにくい文を減らす。
- 接続詞に依存しすぎず、段落内の文を入れ替えても意味が崩れにくい構造にする。
- 重要な用語は初出で定義し、表記ゆれを避ける。

## コードとコマンド

- 読者が写して動かせる全体像を先に示す。抜粋だけでは文脈が欠ける場合は、完全なコードを載せる。
- 詳細説明では該当箇所を再掲し、読者が前のコードへ戻らなくてよい構成にする。
- コメントは情報量を増やすためではなく、注目すべき行へ視線誘導するために使う。
- 複数ファイルを扱う場合は、最初にファイルレイアウトを示す。
- コマンド例は入力、出力、コメントを見分けやすく分ける。

## スクリーンショットと画像

- 初登場の画面や複数ステップの操作は省略しない。
- 本文と画像の両方で操作順序が分かるようにする。
- 理解に不要な余白、隣接 UI、個人情報、通知、ブラウザ枠などのノイズを取り除く。
- UI が変わりやすい場合でも、読者の行動を助ける画像なら掲載を優先する。

## 画像内テキストと言語

- 記事用に生成・編集する画像では、タイトル、軸ラベル、凡例、注釈、吹き出し、矢印ラベル、図中説明を日本語で書く。
- コード、API 名、ライブラリ名、UI 固有の英語表記など、正確性に必要な固有名詞は原文のまま残してよい。
- 日本語が文字化けしないよう、画像生成時は日本語フォントを明示する。
- フォントは `/home/yusuke/.local/share/fonts/codex-japanese/IPAPGothic.ttf` を第一候補にする。存在しない場合は `/home/yusuke/.local/share/fonts/codex-japanese/IPAGothic.ttf`、それも無い場合は `/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf` を使う。

Matplotlib で画像を生成する場合:

```python
from pathlib import Path
from matplotlib import font_manager as fm

FONT_CANDIDATES = [
    "/home/yusuke/.local/share/fonts/codex-japanese/IPAPGothic.ttf",
    "/home/yusuke/.local/share/fonts/codex-japanese/IPAGothic.ttf",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]
FONT_PATH = next(path for path in FONT_CANDIDATES if Path(path).exists())
fm.fontManager.addfont(FONT_PATH)
font_prop = fm.FontProperties(fname=FONT_PATH)

ax.set_title("パレート分布のローレンツ曲線", fontproperties=font_prop)
ax.set_xlabel("累積人口シェア p", fontproperties=font_prop)
ax.set_ylabel("累積所得シェア L(p)", fontproperties=font_prop)
ax.legend(prop=font_prop)
```

Pillow で注釈を追加する場合:

```python
from PIL import ImageFont

font = ImageFont.truetype(FONT_PATH, size=28)
draw.text((x, y), "注目する箇所", font=font, fill=(20, 20, 20))
```

## スクリーンショット処理で使う推奨ツール

- Web 画面を再現して撮影する場合は Playwright を使う。
- 既存画像のサイズ確認、トリミング、注釈付けには Python + Pillow を優先する。
- Pillow が使えない場合は ImageMagick の `identify` / `magick` を使う。
- 画像内テキストの確認が必要な場合だけ OCR を使う。既存環境に `tesseract` がなければ、無理に導入せず目視確認を優先する。
- 画像圧縮は既存プロジェクトに `pngquant`、`oxipng`、`sharp` などがある場合だけ使う。新規依存は勝手に追加しない。
- 画像編集を実行するときは元画像を上書きせず、別名で出力して差し替え可否を確認する。

## スクリーンショット付き画像での Codex 処理

サンプル画像: `../assets/readability-code-element-sample.png`

1. 添付画像またはローカル画像を確認し、必要なら `view_image`、Pillow、ImageMagick で観察する。
2. `file`、Pillow、または ImageMagick で画像形式、幅、高さ、ファイルサイズを確認する。
3. サンプル画像のように、本文で再掲したコード・図の直後に詳細説明が置かれているか確認する。
4. 画像内の矢印、強調枠、注釈テキストが、本文で注目してほしい箇所へ自然に視線誘導しているか確認する。
5. 画像だけを見ても「どこが再掲部分か」「どこを読むべきか」が推測できるか確認する。
6. 本文だけを読んでも再掲箇所の意味が分かるか、画像だけに依存した説明になっていないか確認する。
7. 本文と画像のどちらか片方にしかない情報があれば、もう片方へ補う。
8. 余白、無関係な UI、通知、個人情報、ブラウザ枠、画面の切れ端など読者の注意を逸らす要素を指摘する。
9. 改善案では、トリミング範囲、番号・枠・矢印・注釈を置く位置、本文の修正文を具体的に書く。
10. 実際に画像編集を依頼された場合だけ、Pillow または ImageMagick で編集する。レビューだけなら画像ファイルは変更せず、改善指示として返す。

## 構成と推敲

- 全体像を先に示し、その後で詳細へ進む。
- 関連する本文、コード、図表は近くに置く。
- 長い段落は短い意味単位へ分割し、読み疲れを防ぐ。
- 文章量、コード量、画像量のバランスを見て、読み進めるテンポを崩す箇所を削る。
- レビュー時は「読者がどこで迷うか」を基準に、文章、コード、画像、構成の順で確認する。

## レビュー出力

- 重大な読みづらさから順に指摘する。
- 可能なら改善後の文や見出し案を提示する。
- すぐ直せない画像や外部情報の不足は残課題として明示する。
- 単なる好みではなく、読者の迷い、誤読、手戻りを減らす観点で説明する。

参考: https://zenn.dev/tmknom/articles/readable-github-cicd-book
