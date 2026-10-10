# カリッジュ PC動画の左右拡張（2026-10-10）

現状：素材切出し・設定案・スクリプトを準備済み。必要17ファイル42.64GBを取得・検証済み。17フレームの試験と145フレームの生成がRTX3080 10GBで成功。修正版を作成し、中央145フレームの一致と左右12コマを確認済み。
最新版Wan2GP 17.17 / commit 6479db36bdc2619a904a852bba9c2d78e1a83f82 を別フォルダに用意。旧12.52を保持。
Pythonスクリプトの構文、切出し、中央復元の処理を検証。LTX-2.5生成をこのGPU・この設定で確認済み。

## PowerShellでの実行

このフォルダを作業ディレクトリにする。最新版Wan2GPの専用venvを使用する。

```powershell
$wanPython = 'C:\Users\User\Desktop\Wan2GP-kariju-latest\venv\Scripts\python.exe'
& $wanPython .\pipeline.py check
& $wanPython .\pipeline.py prepare
```

モデル取得は本人の承認後にだけ実行する。必要容量はdownload_manifest.jsonに記載（42.64GB）。
revisionとSHA256を固定し、既存ファイルと同じサイズの物は取得し直さない。
追加依存は新版venvにだけ導入済み。旧venvと旧wgp_config.jsonを変更しない。新環境は旧venvの既存ライブラリを参照するため、旧venvを削除しない。

```powershell
& $wanPython .\pipeline.py download --approved
& $wanPython .\pipeline.py smoke *> .\smoke.log
& $wanPython .\pipeline.py generate *> .\generation.log
# 初回の左右に不要な食品像が出たため、指示とseedを変更して再生成
& $wanPython .\pipeline.py refine *> .\refinement.log
& $wanPython .\pipeline.py finalize
```

大容量の通常取得が止まる場合は、`download_ranges.py --approved`を使用する。
128MiBの範囲を8並列で取得し、完全なファイルのSHA256を検証してから生成へ進む。

smoke成功後のみgenerateを許可する。smoke成功は6秒生成の成功を保証しない。
生成時に不足ファイルがあれば自動ダウンロードをブロックし、そのファイルを確認する。
OOM時は同条件を繰り返さず、まず他のGPUアプリを閉じる。次にスクリプトのFRAMESを73に変更して短尺にする。
短尺化したらprepareを再実行し、finalizeの固定145フレーム表記も実数へ修正する。
解像度を変える場合はcontrolサイズ・配置・復元コードも同時に変更する必要がある。
512×288は高さが64倍数でなく、この版では512×256になる。無確認の設定へ変えない。

## 実際の設定

- model_type: ltx2_25_22B_distilled（base architectureはltx2_25_22B）
- INT8 ConvRot / SDPA / profile 4 / Default VAE / 8 steps / 1 phase
- Control Video process: VG（LTX2 Raw Format / Control Video for Ic Lora）
- video_guide_outpainting: 0 0 0 0 / ratio: 16:9 / denoising_strength: 1
- 1024×576 / 24fps / 145 frames、17 framesで先に動作確認
- 音源なしのAモード。音声生成計算OFFではなく、最終出力から-anで音声を除去
- AIアップスケールOFF。最終1280×720はFFmpegで通常リサイズ
- Negative Promptは受け付けるが、DistilledのCFG=1では抑制効果が限定的

中央復元では同一Control Videoの324×576を生成領域のx350に戻す。
生成結果の寸法・フレーム数・FPSが違えば停止し、時刻を合わせ直す前に調査する。
最終1280×720では元クリップを直接405×720へ縮小し、x438へ配置する。全145フレームのRGBチェックサムを可逆中間MP4で一致確認してからWebエンコードする。
元商品の画角と動作は残す。中央の画質はリサイズとH.264圧縮の影響を受ける。
左右の継ぎ目にぼかしを自動で加えない。必要なら元画像を守った方法を別途検討する。

## 目視確認と納品

AI結果と最終を全長再生し、左右の泡・金属の形・唐揚げや手の重複・ちらつき・中央との継ぎ目を確認。
元動画には撮影時の動きがある。固定カメラの指示は補完に適用するが、実写を残す以上その動きは残る。
不合格なら原因に対応したプロンプト／seed調整で再生成。元動画にない商品を中央へ残さない。
generation_settings.jsonのstatusはencoded_unreviewedで書き出され、12コマの確認後にreviewed_candidateへ更新済み。左右の反射は実写より柔らかいため、共有ページで最終再生確認を行う。

生成成功後のファイル：kariju_pc_outpaint_test.mp4 / kariju_pc_final.mp4 / kariju_pc_poster.jpg / generation_settings.json。
本番サイトのHTML・CSS・JSは変更しない。確認ページの共有は既存GitHub Pagesの専用サブフォルダに限定する。
