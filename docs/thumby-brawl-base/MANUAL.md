# Thumby Brawl Base — 公開マニュアル

## プロジェクトについて

Thumby向けゲームのベースを作りながら、個人で整備しているエージェント用Markdownの作業基準を実開発に適用し、成果を試すポートフォリオ用プロジェクトです。ユーザーが方針と要件を決め、エージェントが実装やテストを支援します。開発は継続中で、完成済みゲームではありません。公開対象はゲームのコードとテスト、利用案内です。

## ゲーム概要

- 対象: 白黒 Thumby（72×40）
- 内容: 3地域・15戦の1対1アクションRPGベース
- 主な要素: 移動と攻撃、ショップと装備、成長、セーブ、短いオープニング／エンディング

## Thumbyで実行する

`ThumbyBrawlBase.py`、`campaign.py`、`rules.py`、`scene_art.py` を同じゲームフォルダーへコピーし、`ThumbyBrawlBase.py` を実行します。ゲーム保存領域の名前は `ThumbyBrawlBase` です。

配布ZIPを作成する場合:

```bash
python3 micropython/Thumby/ThumbyBrawlBase/tools/package_game.py --output /tmp/ThumbyBrawlBase.zip
```

## 操作

- タイトル: Aで新規ゲーム、Bで保存データを読み込み
- 戦闘: 方向ボタンで移動、Aで手攻撃、Bで足攻撃、A+Bで状態表示
- メニュー: 上下で選択、Aで決定、Bで戻る
- 装備: 購入後に装備画面で装着

## テストと確認範囲

PC上のゲームロジック・描画アダプター・入力テストは次のコマンドで実行できます。

```bash
python3 -m unittest discover -s micropython/Thumby/ThumbyBrawlBase -p 'test_*.py' -v
```

2026-10-18時点でPC上のテスト187件が通過し、配布ZIPの生成と整合性も確認しています。PCテストは実機の表示、速度、メモリ使用量、音質、操作感を保証しません。実機確認は継続課題です。

## 公開範囲

このマニュアルでは、公開しているゲームベースの目的、利用方法、確認範囲を説明しています。
