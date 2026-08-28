# 01-game② 2 StreetのBet戦略

## ルール

| 項目 | 内容 |
|---|---|
| OOPハンド | Rank 1〜50（一様ランダム・独立配布） |
| IPハンド | Rank 1〜50（一様ランダム・独立配布） |
| Street | 2 Street |
| 初期Pot | 1 |
| 有効Stack | 4 |
| 許可アクション | Check、Fold、Call、33/100% PotのBet・Raise、All-in |
| 勝敗判定 | 数字が大きい方が勝ち。同じ数字はTie |
| Street遷移 | Check-checkまたはbet-callで同じrankのまま次streetへ進む |
| 利得計算方法 | 初期Potをデッドマネーとし、両者の終端利得の合計は1 |

---

## 最適戦略

### 均衡戦略

#### RootのOOP戦略

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

#### OOP Check後のIP戦略

- 1〜11は100% Pot Bluffを約44〜58%使います。
- 13〜29はほぼCheckです。
- 30〜43はSmall / medium ValueとCheckを混合します。
- 44〜50は100% Potを約63〜64%使い、約35%をCheckへ残します。

IPもNutsを全Betせず、2nd StreetのChecking branchを守ります。1st StreetのCheckはGive upだけでなく、
Delayed value / Bluffを含むため、1 Streetより意味が広くなります。

#### Check-check後の2nd Street戦略

OOPが再びCheckした主要枝では、IPは1〜11をほぼ100% Pot Bluff、39〜50をほぼ100% Pot Valueとして使います。
12〜29はほぼCheck、30〜38はCheckと100% Potを段階的に混合します。最終StreetではFuture optionが消えるため、
1st Streetより明瞭なPolarizationが現れます。

### EV

| プレイヤー | EV |
|---|---:|
| IP | 0.535102767 |
| OOP | 0.464897233 |
| 合計 | 1.00 |

### 導出方法

showdown equity自体はone-street版と同じ$`EQ(r)=(r-0.5)/50`$です。しかし1st-street Action EVには、
現在のFold/Call/Raiseだけでなく、次streetの最適方策から得る継続利得が入ります。例えばrank $`r`$が
1st streetでCheckとBet 100%を混ぜる必要条件は、

$$
EV_r(\mathrm{Check};V_2)
=EV_r(B_{1.0};V_2)
$$

です。$`V_{street\ 2}`$自身が両者のrank別戦略で決まるため、個別混合頻度の短い閉形式はありません。
保存runの数値は全情報集合の無差別条件とbest-response不等式をDCFRで同時に近似したものです。

純粋戦略に近い中位Checkは「現在betしても、より強いcontinue rangeに選別される」ためと説明できます。
nut級のCheckは、2nd streetまで含むchecking rangeを守り、IPのdelayed aggressionから追加利得を得ます。

---

## ポーカーにおける概念理解

### 同じAction abstractionでの1 Street比較

| Street数 | IP EV | OOP EV | Exploitability |
|---:|---:|---:|---:|
| 1 | 0.531675531 | 0.468324469 | `1.7038e-6` |
| 2 | 0.535102767 | 0.464897233 | `5.8126e-6` |

この設定では2 street化によりIP EVが約0.00343増えました。positionを持つIPは、OOPの1st-street actionを
観察してからrangeを絞り、delayed betと2nd barrelを選べます。一方でOOPも2nd streetを先にbetできるため、
「streetを増やせば必ずIPが得をする」という一般定理ではありません。対称AKQの離散例では逆方向の結果も出ています。

この結果から、Future streetがDelayed aggression、Checking-range protection、StreetごとのPolarizationを
生むことを確認できます。

---

## Solverによる再現結果

| 指標 | 結果 |
|---|---:|
| IP EV | 0.535102767 |
| OOP EV | 0.464897233 |
| Exploitability | `5.8126e-6` |

- [Strategy Viewer](../../public/studies/zero_one_n50_two_street/strategy_viewer.html)
- [計算条件](../../public/studies/zero_one_n50_two_street/resolved_config.json)

### 再現方法

```bash
toy-poker run configs/experiments/study_zero_one_n50_two_street_dcfr.toml
```

---

## その他備考

### 7サイズ版を採用しなかった理由

one-street studyと同じ10/20/33/50/75/100/150%を2 streetへ展開すると、public nodeは97,057、
information setは1,673,600になります。10 iterationの実測wall timeが約12.9秒で、1万iterationと
全node解析は教材の標準runとして過大でした。このstudyは33%/100%へaction abstractionを粗くしています。
したがって、[7サイズのone-street結果](study_12_01_game_01_oop_bet_strategy.md)とのEV差をstreet効果だけとして比較してはいけません。
