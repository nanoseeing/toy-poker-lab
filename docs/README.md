# Documentation guide

このプロジェクトでは、ルール、実験設定、計算結果を別々の責務として管理します。

| 場所 | 役割 | 更新タイミング |
|---|---|---|
| ルート `README.md` | 導入、最短の実行方法、文書への入口 | CLIや導入方法を変更したとき |
| `docs/games/<game_id>.md` | ゲームのルール、情報構造、パラメータ、ペイオフ、解析解 | ゲーム仕様を変更したとき |
| `docs/games/README.md` | 利用可能なゲームのカタログ | ゲームを追加・削除したとき |
| `docs/experiments.md` | 全ゲーム共通のTOML、CLI、artifact仕様 | 実験基盤を変更したとき |
| `docs/solvers.md` | solver更新則、データ配置、高速化・benchmark方針 | solverを変更したとき |
| `docs/studies/*.md` | 最適戦略、数学的導出、solver再現、実戦への応用 | 教材または代表実験を追加したとき |
| `configs/experiments/*.toml` | そのまま実行できる実験設定 | 標準実験を追加・変更したとき |
| `artifacts/<game>/<run-id>/` | 方策、生データ、図、run固有レポート | 実験実行時に自動生成 |
| `src/toy_poker/games/` | OpenSpielが実行する機械可読な仕様 | 実装変更時 |

`artifacts` は生成物であり、ゲームルールの正本にはしません。逆にゲーム文書には、
特定runの丸められた数値を固定的にコピーせず、一般式、デフォルト値、再現コマンドを
記載します。

## 新しいゲームを追加するとき

1. `src/toy_poker/games/<game_id>/` にゲームとメタデータを実装する。
2. `src/toy_poker/games/registry.py` にプラグインを登録する。
3. `configs/experiments/<game_id>_<solver>.toml` を追加する。
4. [`docs/games/_template.md`](games/_template.md)からゲーム文書を作成する。
5. [`docs/games/README.md`](games/README.md)の一覧へ追加する。
6. ルール、ペイオフ、解析、solver、統合テストを追加する。

ルール変更時はコードだけでなく、ゲーム文書、標準TOML、解析解、テストを同じ
コミットで更新します。
