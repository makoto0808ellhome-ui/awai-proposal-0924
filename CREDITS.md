# 写真・フォント・ライブラリの出典

取得・確認：2026-09-24。すべてローカルの提案用試作に使用。実店舗の商品写真ではありません。

## 採用写真

| ファイル | 写真・撮影者 | 出典 |
| --- | --- | --- |
| assets/hero.webp | 唐揚げの寄り・ibmoon Kim | [Unsplash](https://unsplash.com/photos/a-plate-of-food-on-a-table-with-a-glass-of-beer-ydH1nhQks4Q) |
| assets/boneless.webp | 骨なし唐揚げ・Dennis Zhang | [Unsplash](https://unsplash.com/photos/a-white-plate-topped-with-fried-food-on-top-of-a-wooden-table-TTupRwxPgoA) |
| assets/basket.webp | 籠に入った唐揚げ・Kouji Tsuru | [Unsplash](https://unsplash.com/photos/karaage-fried-chicken-with-dipping-sauce-au6niQKtYCs) |
| assets/wings.webp | 日本風の手羽先・Do mee | [Unsplash](https://unsplash.com/photos/cooked-food-p57xcIEhYFs) |
| assets/bento.webp | 唐揚げ弁当・Ryutaro Tsukata | [Pexels](https://www.pexels.com/photo/fried-chicken-with-rice-and-sauce-6249394/) |

- [Unsplash License](https://unsplash.com/license)：無料で商用利用可能、クレジット不要。採用4点の公開写真データで `plus: false` と `premium: false` を確認。
- [Pexels License](https://www.pexels.com/license/)：無料利用・変更可能、クレジット不要。写真ページの無料ダウンロードとライセンス表示を確認。
- 手羽先のタレやごま、弁当の副菜・個数は実商品を示しません。写真にはイメージ表示を付け、全ページの下部にも無料素材の仮写真と記載。
- WebP変換、表示枠に合わせたトリミングだけを実施。生成画像は使用していません。
- 適切な写真を優先し、採用は5点。お店の外観、チュロス、つけダレは灰色の枠。キッズ・1キロ弁当は内容と写真の未確定表示。
- `work/` 内の候補写真は比較用で、サイトには使用しません。店舗名入り容器、別料理を含む弁当、一般的な手羽先と形状の違うものなどは不採用。

## ロゴ

本人が用意した `photos/logo.jpg` から軽量版 `assets/logo.webp` を作成。徳島本店の店舗欄に使用。藍住店には使っていません。Instagramからの自動取得はしていません。

## フォント

- M PLUS Rounded 1c 900 — [Google Fonts](https://fonts.google.com/specimen/M+PLUS+Rounded+1c)
- Noto Sans JP 400 / 700 — [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+JP)
- SIL Open Font License 1.1。ライセンス文を `assets/fonts/rounded-OFL.txt`、`assets/fonts/noto-OFL.txt` に同梱。
- 必要な文字だけを保存したローカル版。表示文言を増やす場合は `tools/prepare-fonts.mjs` で再取得するか、システムフォントのフォールバックを使います。

## 動き

- [GSAP 3.12.5](https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js)
- [ScrollTrigger 3.12.5](https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js)
- [Lenis 1.1.13](https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js)

CDNからSRI付きで取得。SHA-384値は `assets/vendor/manifest.json` に保存。ネット接続できない場合は同じファイルのローカル版を使います。減らす設定では読み込まず、文字・価格は通常表示します。

## 店舗情報

主な掲載内容は本人から渡された設計図。確認時の差異と参照サイトは `参考メモ.md` を参照。本部サイトの文章・画像は転載していません。
