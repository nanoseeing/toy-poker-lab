# 基礎① ゲーム理論の基本用語

この文書は、各Studyで使うゲーム理論とソルバーの用語を、toy pokerを読むために必要な順序で説明します。
ポーカーは、偶然によるカード配布、相手から見えないprivate hand、複数回の意思決定を含むため、
**不完全情報の展開形ゲーム**として扱います。

---

## 展開形ゲームの構成要素

展開形ゲームは、誰が、どの情報を持ち、どの順序で行動し、最後にどの利得を受け取るかをゲーム木で
表したものです。

| 用語 | 意味 | このプロジェクトでの例 |
| --- | --- | --- |
| プレイヤー | 意思決定を行う主体 | OOPとIP |
| chance node | 既知の確率に従って結果を選ぶ、プレイヤー以外のnode | private handの配布 |
| action | ある局面で選べる行動 | Check、Bet、Call、Raise、Fold |
| 履歴 | rootから現在までのchance結果とaction列 | `deal K → OOP Check → IP Bet 50%` |
| node | ある完全な履歴に対応するゲーム木上の局面 | root、Betに直面した局面など |
| 終端ノード | 勝敗と利得が確定し、それ以上actionがないnode | Fold後、showdown後 |
| 利得 | 終端ノードで各プレイヤーが受け取る数値 | potの獲得額から追加投入額を引いた値 |
| 情報集合 | 行動するプレイヤーから区別できないnodeの集合 | 自分のhandと公開履歴は同じだが、相手handが異なる局面 |
| 完全記憶 | 自分が過去に知っていた情報と行ったactionを忘れない性質 | このプロジェクトの全toyゲーム |

### 不完全情報と情報集合

実際のゲーム木の一つのnodeには、両者のprivate handを含む完全な状態があります。しかしプレイヤーは
相手のhandを観察できません。そのため、同じ自分のhandと公開履歴を持つ複数のnodeを一つの情報集合として
扱い、その情報集合内では同じ戦略を選ばなければなりません。

### 定和ゲーム

このプロジェクトでは初期pot 1を誰の拠出ともみなさないデッドマネーとして扱います。そのため、全ての
終端ノードでOOPとIPの利得合計は1です。これはゼロ和ではなく定和ですが、各プレイヤーの利得から
定数0.5を引けばゼロ和表現になり、最適戦略とNash均衡は変わりません。

---

## 戦略

### 戦略

戦略は、自分が行動する**全ての情報集合**で何をするかを定めた完全な行動計画です。実際には到達しない
情報集合での行動も戦略に含まれます。全プレイヤーの戦略をまとめたものを戦略プロファイル
$`\sigma=(\sigma_{\mathrm{OOP}},\sigma_{\mathrm{IP}})`$と呼びます。

### 純粋戦略

純粋戦略は、各情報集合で一つのactionを100%選びます。`Aで100% All-in`や`Kで100% Check`は、
純粋戦略を構成する一部の指定です。

### 混合戦略

混合戦略は、複数の**完全な純粋戦略**から、ゲーム開始時に一つを確率的に選ぶ戦略です。

### 行動戦略

行動戦略は、情報集合へ到達するたびに、その場で各actionを選ぶ確率を定めます。情報集合 $`I`$ で
action $`a`$ を選ぶ確率を、

$$
\sigma_i(I,a)
$$

と表します。Strategy Viewerの`Q: All-in 50% / Check 50%`や、CFRが出力する戦略は行動戦略です。

完全記憶を持つ有限ゲームでは、混合戦略と行動戦略は、終端へ到達する確率と期待利得の意味で互いに
再現できます。以下では、各情報集合でのaction頻度を直接表す行動戦略を扱います。

### Support

ある情報集合で正の確率を与えられているactionの集合をsupportと呼びます。

混合頻度を数学的に導出するときは、どのactionがsupportに入るかを先に仮定し、最後にその仮定が
正しいかを検証します。

---

## 期待利得、最適反応、Nash均衡

### 期待利得

戦略プロファイル $`\sigma`$ に従ったプレイヤー $`i`$ の期待利得を $`u_i(\sigma)`$ と書きます。これは、
chance結果と両者の確率的actionが作る全終端ノードの利得を、reachで重み付けした平均です。

### 最適反応

最適反応は、相手の戦略 $`\sigma_{-i}`$ を固定したとき、自分の期待利得を最大にする戦略です。数式では
best responseの略として $`BR_i`$ と書きます。

$$
u_i(BR_i(\sigma_{-i}),\sigma_{-i})
=\max_{\sigma_i'}u_i(\sigma_i',\sigma_{-i})
$$

最適反応は一意とは限りません。複数のactionが同じ最大EVを持つなら、そのどれを選んでも最適反応です。

### Nash均衡

戦略プロファイル $`\sigma^{\star}`$ がNash均衡であるとは、全プレイヤーについて、単独で戦略を変更しても
期待利得を増やせないことです。

$$
u_i(\sigma_i^{\star},\sigma_{-i}^{\star})
\geq
u_i(\sigma_i',\sigma_{-i}^{\star})
\qquad
\text{for all }\sigma_i'
$$

2人ゼロ和または定和ゲームでは、全てのNash均衡が同じ均衡利得、すなわちゲームの値を持ちます。
一方、同じゲームの値を実現する均衡戦略は複数存在する場合があります。

### 無差別条件と未使用action

到達可能な情報集合 $`I`$ で複数actionを正の頻度で使うなら、それらは全て最大のAction EVを持ちます。

$$
\sigma_i(I,a)>0
\quad\Longrightarrow\quad
V_i(I,a)=\max_{a'}V_i(I,a')
$$

使用しないactionについて必要なのは、そのEVがsupport内のactionを上回らないことです。

$$
\sigma_i(I,a)=0
\quad\Longrightarrow\quad
V_i(I,a)\leq\max_{a'}V_i(I,a')
$$

各Studyでは次の順序で行動戦略の混合頻度を導出します。

1. supportに入るactionを仮定する。
2. 相手のprivate handごとに各actionの利得を書く。
3. カード確率と相手の行動頻度で期待利得を作る。
4. support内のAction EVを等置する。
5. 得られた頻度が0から1に入り、未使用actionのEVが最大値以下であることを確認する。

---

## reach、Bayes更新、off-path

reach（reach probability）は、ある履歴またはnodeへ戦略に従って到達する確率です。完全な履歴 $`h`$ への
reachは、chance、OOP、IPがその履歴までに選んだ確率の積です。

$$
\pi^\sigma(h)=
\pi_c(h)
\pi_{\mathrm{OOP}}^\sigma(h)
\pi_{\mathrm{IP}}^\sigma(h)
$$

情報集合 $`I`$ に複数の完全履歴が含まれるとき、プレイヤーは観察した情報から、その中のどの履歴にいるかを
条件付き確率として推定します。reachが正なら、Bayes則により、

$$
\mu^\sigma(h\mid I)=
\frac{\pi^\sigma(h)}
{\sum_{h'\in I}\pi^\sigma(h')}
\qquad h\in I
$$

となります。ポーカーでは、これは公開されたaction履歴を観察した後の相手のconditional rangeに相当します。

### Counterfactual reach

CFRではプレイヤー $`i`$ 自身が情報集合までに選んだ確率を除き、chanceと相手だけによるreach確率を使います。

$$
\pi_{-i}^\sigma(h)=
\pi_c(h)\prod_{j\ne i}\pi_j^\sigma(h)
$$

これにより、「自分がその情報集合へ必ず到達したと仮定したとき、そこで別のactionを選べばどれだけ
改善したか」を測れます。

### Off-path戦略

均衡戦略でreachが0になる情報集合をoff-pathと呼びます。Nash均衡はゲーム開始時点からの単独逸脱を
防ぎますが、reachが0の情報集合での行動を一意に決めるとは限りません。とくにchanceと相手による
counterfactual reachも小さい情報集合ではCFRの更新量が小さく、個別の混合頻度が遅く収束する場合があります。
一方、自分自身の過去のactionだけが低reachの原因なら、CFRは自分のreachを除いてregretを更新します。

---

## ExploitabilityとNashConv

Exploitabilityは、現在の戦略が最適反応によってどれだけ攻略され得るかを表す量です。各プレイヤーが現在の
相手戦略に対する最適反応へ変更したときの改善幅を合計したものがNashConvです。

$$
\mathrm{NashConv}(\sigma)=
\sum_i
\left[
u_i(BR_i(\sigma_{-i}),\sigma_{-i})-u_i(\sigma)
\right]
$$

本プロジェクトの2人定和ゲームでは、その平均をExploitabilityとして表示します。

$$
\mathrm{Exploitability}(\sigma)=
\frac{\mathrm{NashConv}(\sigma)}{2}
$$

0ならNash均衡であり、小さいほど均衡に近いことを意味します。単位は利得と同じで、このプロジェクトでは
初期pot 1に対する値です。例えば $`10^{-5}`$ は、各プレイヤーの最適反応による改善幅を平均すると
初期potの0.001%であることを表します。

全体のExploitabilityが小さくても、低reachの情報集合の個別戦略まで安定しているとは限りません。
個別頻度を読むときはreach、Action EV、近接するcheckpointでの変化も確認します。

---

## Counterfactual regretとCFR

反復 $`t`$ の情報集合 $`I`$ で、現在の行動戦略に対してaction $`a`$ を選び続けた場合の反実仮想的な改善幅を、

$$
r_i^t(I,a)=
v_i(\sigma_{I\to a}^t,I)-v_i(\sigma^t,I)
$$

と書きます。これを反復にわたって加算したものがcumulative counterfactual regretです。

$$
R_i^T(I,a)=\sum_{t=1}^{T}r_i^t(I,a)
$$

CFR（Counterfactual Regret Minimization）は、各情報集合で正のcumulative regretに比例して次の行動戦略を作る
regret matchingを行います。全情報集合のcounterfactual regretを小さくすることで、2人ゼロ和ゲームの
**平均戦略**をNash均衡へ近づけます。

- CFR+：cumulative regretの負の部分を0へ切り上げるregret matching+と、重み付き平均戦略を使います。
- DCFR（Discounted CFR）：古い正負のregretと平均戦略への寄与を割り引き、最近の反復を相対的に重く扱います。

したがって、ソルバーの出力を評価するときは、通常、探索中の現在戦略ではなく平均戦略の
期待利得とExploitabilityを確認します。実装と性能方針は[ソルバー構成](../solvers.md)で説明します。

---

## Node lock

Node lockは、特定の情報集合・handの行動戦略を外部から固定し、残りだけを最適化する機能です。lock付き結果は
元ゲーム全体のNash均衡ではなく、固定した戦略からの逸脱を許さない**制約付きゲームの均衡**です。

- 期待利得：実際のlock済み戦略プロファイルの利得
- Constrained Nash gap（`constrained_nash_gap`）：lockを守る戦略集合内での最適反応による改善幅
- Unconstrained Exploitability（`unconstrained_exploitability`）：lockを破る逸脱も許した、元ゲームに対するExploitability

lockが元ゲームの均衡戦略と異なる場合、constrained Nash gapは0へ近づいても、unconstrained Exploitabilityは
0になりません。

---

## 読み方の要点

- 戦略は、到達しない情報集合を含む完全な行動計画です。
- ViewerとCFRの確率表は、厳密には各情報集合の行動戦略です。
- 正の頻度で混ぜるactionは最大Action EVを共有し、未使用actionはそれ以下です。
- 均衡利得が一意でも、均衡戦略やoff-pathの混合頻度は一意とは限りません。
- Exploitabilityは戦略全体の指標であり、個別nodeの収束保証ではありません。

次に[ポーカー用語と計算](study_02_poker_terms_and_math.md)で、range、EV、EQ、EQR、MDF、
polarization、Position、geometric bettingを確認してください。

---

## 参考資料

- [MIT OpenCourseWare: Extensive Games with Perfect Recall](https://ocw.mit.edu/courses/17-810-game-theory-spring-2021/mit17_810s21_lec4.pdf)
- [Regret Minimization in Games with Incomplete Information](https://papers.nips.cc/paper_files/paper/2007/hash/08d98638c6fcd194a4b1e6992063e944-Abstract.html)
- [Solving Heads-Up Limit Texas Hold'em with CFR+](https://www.ijcai.org/Proceedings/15/Papers/097.pdf)
- [Discounted Regret Minimization](https://ojs.aaai.org/index.php/AAAI/article/view/4007)
- [OpenSpiel concepts](https://github.com/google-deepmind/open_spiel/blob/master/docs/concepts.md)
