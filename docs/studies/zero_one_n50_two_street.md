# 0–1 game approximation: N=50, two streets

> Status: `数値検証済み`・戦略解釈は`考察`

## ルール

| 項目 | 内容 |
|---|---|
| Street | 2 street。public runoutなし |
| OOP range | rank 1〜50を一様に保有 |
| IP range | rank 1〜50を一様に保有 |
| 配布 / 強さ | 独立配布。数字が大きいほど強く、同rankはtie |
| 初期pot / stack | pot 1、両者stack 4 |
| Bet / Raise size | 33% pot、100% pot、All-in |
| Raise制約 | 標準minimum raise。両者Raise可能 |
| Street遷移 | Check-checkまたはbet-callで同じrankのまま次streetへ進む |
| Dynamic equity | public cardがないため変化しない |
| 利得 | 終端利得の合計は常に1 |

## Root OOP戦略

主要な構造は次のとおりです。数値は4,000 iteration時点で、EV差がexploitabilityと同程度の混合は
一意な意味を持たないことに注意してください。

| Rank帯 | 主要戦略 |
|---|---|
| 1–11 | Checkを中心に、33%/100% bluffを混合 |
| 12–37 | ほぼ100% Check |
| 38 | 100% Bet 33% |
| 39 | Bet 33% 26.8%、残りCheck |
| 40–43 | ほぼ100% Check |
| 44–50 | Checkを約62〜72%残し、主に100% betを混合 |

低rankはFold equityを作るbluff、中位rankはshowdown/check、38〜39はthin value、44以上は
strong valueとchecking-range protectionを担います。nut級をすべてbetしないため、OOPはCheck後も
IPの2 street aggressionへCall/Raiseできるrangeを保持します。

## 数学的な検証範囲

showdown equity自体はone-street版と同じ$EQ(r)=(r-0.5)/50$です。しかし1st-street Action EVには、
現在のFold/Call/Raiseだけでなく、次streetの最適方策から得る継続利得が入ります。例えばrank $r$が
1st streetでCheckとBet 100%を混ぜる必要条件は、

$$
EV_r(\mathrm{Check};\,V_{street\ 2})
=EV_r(\mathrm{Bet\ 100\%};\,V_{street\ 2})
$$

です。$V_{street\ 2}$自身が両者のrank別戦略で決まるため、個別混合頻度の短い閉形式はありません。
保存runの数値は全情報集合の無差別条件とbest-response不等式をDCFRで同時に近似したものです。

純粋戦略に近い中位Checkは「現在betしても、より強いcontinue rangeに選別される」ためと説明できます。
nut級のCheckは、2nd streetまで含むchecking rangeを守り、IPのdelayed aggressionから追加利得を得ます。

## OOP Check後のIP

- 1〜11は100% pot bluffを約44〜58%使います。
- 13〜29はほぼCheckです。
- 30〜43はsmall/medium valueとCheckを混合します。
- 44〜50は100% potを約63〜64%使い、約35%をCheckへ残します。

IPもnutsを全betせず、2nd streetのchecking branchを守ります。1st streetのCheckはgive upだけでなく、
delayed value/bluffを含むため、one-streetより意味が広くなります。

## Check-check後の2nd street

OOPが再びCheckした主要枝では、IPは1〜11をほぼ100% pot bluff、39〜50をほぼ100% pot valueとして使います。
12〜29はほぼCheck、30〜38はCheckと100% potを段階的に混合します。最終streetではfuture optionが消えるため、
1st streetより明瞭なpolarizationが現れます。

## 同じaction abstractionでの1 street比較

| Street数 | IP EV | OOP EV | Exploitability |
|---:|---:|---:|---:|
| 1 | 0.531675531 | 0.468324469 | `1.7038e-6` |
| 2 | 0.535102767 | 0.464897233 | `5.8126e-6` |

この設定では2 street化によりIP EVが約0.00343増えました。positionを持つIPは、OOPの1st-street actionを
観察してからrangeを絞り、delayed betと2nd barrelを選べます。一方でOOPも2nd streetを先にbetできるため、
「streetを増やせば必ずIPが得をする」という一般定理ではありません。対称AKQの離散例では逆方向の結果も出ています。

## Solver結果

| 指標 | 結果 |
|---|---:|
| Public decision nodes | 280 |
| Iterations | 4,000 / 10,000 |
| Exploitability | `5.8126e-6` |
| IP EV | 0.535102767 |
| OOP EV | 0.464897233 |
| Solver計算時間 | 約1.56秒 |

- [Strategy Viewer](../../public/studies/zero_one_n50_two_street/strategy_viewer.html)
- [計算条件](../../public/studies/zero_one_n50_two_street/resolved_config.json)

## 7サイズ版を採用しなかった理由

one-street studyと同じ10/20/33/50/75/100/150%を2 streetへ展開すると、public nodeは97,057、
information setは1,673,600になります。10 iterationの実測wall timeが約12.9秒で、1万iterationと
全node解析は教材の標準runとして過大でした。このstudyは33%/100%へaction abstractionを粗くしています。
したがって、[7サイズのone-street結果](zero_one_n50_one_street.md)とのEV差をstreet効果だけとして比較してはいけません。

## 実戦への応用と限界

この結果から観察できるのは、future streetがdelayed aggression、checking-range protection、
streetごとのpolarizationを生むことです。実カードのblocker、board runout、dynamic equityはなく、
rankごとの細かな混合は離散化とaction abstractionに依存します。

## 再現方法

```bash
toy-poker run configs/experiments/study_zero_one_n50_two_street_dcfr.toml
```
