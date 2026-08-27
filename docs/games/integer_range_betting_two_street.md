# Integer 1-N two-street custom-size game

## ルール概要

- OOP/IPへ1〜Nのprivate rankを独立に配り、大きい数字を強いものとします。
- 初期potは1、残りstack、rank weight、bet/raise pot比率を設定できます。
- 両streetともOOPから開始し、Check、Bet、Raise、Call、Fold、All-inを使用できます。
- 1st streetのCheck-checkまたはbet-callで、同じrankのまま2nd streetへ進みます。
- Fold、All-in-call、または2nd streetのCheck-check/bet-callで終了します。
- public cardは増えないためfuture-street option valueはありますがdynamic equityはありません。

## toyゲームの目的

one-street版と同じrange・sizeを保ちながら、将来streetの存在だけがpolarization、barrel頻度、
checking range、equity realizationへ与える影響を比較します。複数streetで同じpot比率を使う
geometric bettingと、early-street bluffの一部が次streetでgive upする構造を検証できます。

private rankは独立配布なのでblockerはありません。またrunoutがなくhand strengthが固定されるため、
実戦のdynamic equityではなく純粋なbetting option valueを扱うゲームです。

## パラメータ

one-street版の`oop_stack`、`ip_stack`、`num_ranks`、OOP/IP別rank weight、`bet_fractions`、
`oop_can_raise`、`ip_can_raise`を共通で使用します。初期pot 1とstreet数2は固定です。

## Street遷移

1st streetで両者のcommitが等しくなって次streetへ進んでも、commitとpotは維持します。
minimum raise incrementだけは新しいstreetで0へ戻します。2nd streetもOOPから開始します。

例えば初期pot 1、stack 4でpot bet-callすると、両者commit 1、pot 3で2nd streetへ進みます。
そこでpot-sized bet 3をCallすると、両者の合計commitは4となりAll-inです。

## Showdownと利得

両者の最終commitを $c$ とすると、勝者は $1+c$、敗者は $-c$、tieは両者0.5です。
Fold側のcommitが $c_f$ ならFold側は $-c_f$、勝者は $1+c_f$ です。利得合計は常に1です。

## 設定と実行

```bash
toy-poker run configs/experiments/integer_range_betting_two_street_cfr_plus.toml
```

標準設定はN=10、stack 4、33%/100% pot、standard minimum raise、C++ range DCFRです。

- [公開Report](../../public/results/integer_range_betting_two_street/report.md)
- [公開Strategy Viewer](../../public/results/integer_range_betting_two_street/strategy_viewer.html)
- [N=50 study](../studies/zero_one_n50_two_street.md)

## 出力の読み方

Viewerのhistoryとpot panelでstreet、残stack、過去streetのcommitを確認します。低到達確率の
2nd-street branchは、頻度だけでなくAction EVとreach warningを合わせて読みます。

## 実装とテスト

- [共通2-street state](../../src/toy_poker/games/fixed_range_two_street.py)
- [ゲーム実装](../../src/toy_poker/games/integer_range_betting_two_street/game.py)
- [テスト](../../tests/games/test_integer_range_betting_two_street.py)
