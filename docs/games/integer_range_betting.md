# Integer 1-10 custom-size game

## 概要

OOPとIPへ1〜10の整数を独立かつ等確率で配り、1 streetでpot比率のbetとraiseを
繰り返せる有限定和ゲームです。数字が大きい方がshowdownで勝ち、同じ数字はtieです。

初期potはデッドマネーの1、両者のstackはデフォルト4です。標準サイズとして33%と
100% potのbet/raise、およびAll-inを使用します。通常のno-limitと同じminimum raise
制約を適用します。

## プレイヤーと情報構造

| OpenSpiel index | 名前 | private number | 行動順 |
|---:|---|---|---|
| 0 | IP | 1〜10を各10% | OOPの後 |
| 1 | OOP | 1〜10を各10% | 最初 |

両者の数字は独立なので、100通りの組を各1%でdealします。各プレイヤーは自分の数字、
公開action履歴、pot、commit額を知りますが、相手の数字は知りません。

## パラメータ

| 名前 | 型 | デフォルト | 制約 | 意味 |
|---|---|---:|---|---|
| `oop_stack` | float | 4.0 | `> 0` | OOPの残りstack |
| `ip_stack` | float | 4.0 | `> 0` | IPの残りstack |
| `bet_fractions` | string | `"0.3333333333333333,1.0"` | 正数、有限、重複なし | 使用できるpot比率 |

`bet_fractions`はOpenSpielのparameterとして渡せるよう、カンマ区切り文字列で指定します。
読み込み時に数値へ変換し、昇順に正規化します。標準の1/3は表示上`33%`とします。

実効stackは次のとおりです。

\[
S=\min(\text{oop\_stack},\text{ip\_stack})
\]

heads-upでは相手がcoverできない超過分を返却できるため、commit額を実効stackまでに
制限します。

## ゲーム進行と合法アクション

1. OOPとIPへ数字をdealする。
2. OOPから1 streetのbettingを開始する。
3. Check-check、Call、Foldのいずれかで終了する。
4. CallまたはCheck-checkならshowdownする。

| 状況 | 合法アクション |
|---|---|
| betされていない | `Check`、各`Bet x%`、`All-in` |
| 通常bet/raiseに直面 | `Fold`、`Call`、合法な各`Raise x%`、`Raise all-in` |
| All-inに直面 | `Fold`、`Call` |

計算したカスタムサイズが残りstack以上なら同値actionを重複させず、`All-in`だけを
表示します。

## Bet・Raiseサイズ

未bet時のfraction \(x\) によるbet額は、action前のpotを \(P\) として次のとおりです。

\[
\text{bet}=xP
\]

raise時は、現在のcall必要額を \(C\)、相手のbetを含む現在potを \(P_{current}\) とします。

\[
P_{after\ call}=P_{current}+C
\]

\[
\text{chips added}=C+xP_{after\ call}
\]

相手のbet前のpotを \(P\)、相手のbet額を \(B\) と置けば、\(C=B\)、
\(P_{current}=P+B\)なので、同じ式は次の形になります。

\[
B+x(P+2B)
\]

## Minimum raise

カスタムraiseによるwager levelの増額は、直前のfull bet/raiseによる増額以上でなければ
なりません。これを満たさないカスタムraiseは非合法です。

stack上限によるAll-inだけはminimum未満のshort raiseを許可します。heads-upで相手は
その後`Call`または`Fold`するため、reopen判定は必要ありません。

例として初期pot 1へpot-sizeの1をbetされた場合、1/3 pot raiseは次の額になります。

\[
1+\frac{1}{3}(1+2)=2
\]

raise incrementは1で直前のbet increment 1と等しいため、minimum raiseを満たします。

## Showdownとutility

両者が追加で \(c\) ずつcommitしている場合は次のとおりです。

| 結果 | IP utility | OOP utility |
|---|---:|---:|
| IPの数字が大きい | \(1+c\) | \(-c\) |
| OOPの数字が大きい | \(-c\) | \(1+c\) |
| tie | 0.5 | 0.5 |

Fold側が \(c_f\) commitしている場合、Fold側は \(-c_f\)、勝者は \(1+c_f\) です。
すべてのterminalでutility合計は初期pot額の1になります。

## 設定と実行

標準設定は
[`configs/experiments/integer_range_betting_cfr_plus.toml`](../../configs/experiments/integer_range_betting_cfr_plus.toml)
です。

```toml
[game]
id = "integer_range_betting"

[game.params]
oop_stack = 4.0
ip_stack = 4.0
bet_fractions = "0.3333333333333333,1.0"

[solver]
id = "cfr_plus"
backend = "native_efg"
iterations = 100000
snapshot_every = 10000
```

```bash
toy-poker run configs/experiments/integer_range_betting_cfr_plus.toml
```

## 標準設定の参考結果

stack 4、標準サイズ、`native_efg` CFR+を100,000反復した結果は次のとおりです。

| 指標 | 結果 |
|---|---:|
| IP EV | 0.5320656337 |
| OOP EV | 0.4679343663 |
| Exploitability | 0.000000286056 |
| NashConv | 0.000000572112 |
| 計算時間 | 約278.4秒 |

保存したcheckpoint中の最良Exploitabilityは100,000反復時点の約`0.000000286056`でした。
主要なrange構造は次のようになりました。

- OOPは2〜6をほぼ常にCheckし、7〜8をほぼ常に33% Betしました。
- OOPの1は33%・100% Betを混ぜたbluff、9〜10はCheckとvalue betを混ぜました。
- OOPのCheck後、IPは3〜6をほぼ常にCheckしました。
- IPの8〜10は主にvalue bet、1は主に100% Betのbluff、2はCheckとbluffを混ぜました。

数値はCFR+による均衡近似です。個々の低到達確率局面や非一意な混合は、HTMLの
reach probability、Action EV、Exploitabilityと併せて解釈してください。

## 解析と出力

閉形式の均衡解は設定していません。CFR+のExploitability、NashConv、Player EV、
information setごとのAction EVで収束を確認します。

数字1〜10を比較しやすくするため、strategyとAction EVは、private numberを列、actionを
行、公開履歴をパネルとするヒートマップで出力します。HTML後段のfull information set表と
CSVには低到達確率局面を含む全データを残します。100通りのprivate dealは、action tree上
では到達確率で重み付けした1本のpublic treeへ集約します。

小さいfractionを多数追加するとraise回数とゲーム木が急増します。標準の1/3・1.0、
stack 4では約12,900ノードです。

## 実装とテスト

- [ゲーム定義](../../src/toy_poker/games/integer_range_betting/game.py)
- [共通1 street状態機械](../../src/toy_poker/games/fixed_range_one_street.py)
- [表示用plugin](../../src/toy_poker/games/integer_range_betting/plugin.py)
- [ゲームルールテスト](../../tests/games/test_integer_range_betting.py)
- [解析・native EFGテスト](../../tests/analysis/test_integer_range_betting_analysis.py)
