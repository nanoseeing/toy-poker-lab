# Solver architecture and performance policy

## 採用方針

小規模toy gameではOpenSpielのC++ `CFRPlusSolver`を独立した参照実装として使います。
integer 1-N weighted-range gameでは、private dealのN²列挙を避けるため、public betting treeと
rank vectorを分離したfull-tree CFRを使います。既定の高速経路は`cpp_range`、更新則は
`dcfr`です。

| 層 | 実装 | 役割 |
|---|---|---|
| 独立oracle | OpenSpiel `native_efg` CFR+ | 小さい木でutility・方策・Exploitabilityを照合 |
| 読みやすい参照 | NumPy `vectorized_range` | CFR+/DCFR式とrange評価を検証 |
| 実運用 | C++20 `cpp_range` | flat public tree、連続rank配列、allocation-free traversal |
| checkpoint | Python/NumPy exact evaluator | Expected Returns、best response、Exploitabilityをfloat64評価 |

`cpp_range`はregret matching+、alternating updates、linear averagingを用いるCFR+と、
`DCFR(1.5, 0, 2)`を実装します。DCFRでは正・負の累積regretを別々にdiscountし、平均方策も
discountします。

## データ配置

public treeはnodeごとのPython objectではなく、`players`、`action_offsets`、`children`、
terminal metadataからなるCSR風structure-of-arraysへ一度だけ変換します。regret、現在方策、
平均方策は`[public action slot, private rank]`の連続配列です。反復中のchild EVとreachは
最大tree depth分のarenaを再利用し、node/actionごとのheap allocationを行いません。

showdown EVはrank順のprefix sumで計算するため、各terminalでO(N²)ではなくO(N)です。
OOPとIPの非一様rangeは別々の確率vectorとしてterminal counterfactual valueへ入ります。

## 精度

`precision="float64"`はregret・strategyもdoubleで保持する基準モードです。
`precision="float32"`はこの3配列だけをfloatへ圧縮し、EV、reach、terminal集計、checkpoint
評価はdoubleのままです。大規模木では状態メモリを半減できますが、丸めによって均衡の
非一意な混合や収束経路は変わり得るため、最終品質は必ずfloat64 Exploitabilityで判定します。

## 現時点で採用しない最適化

- MCCFR: 現在のpublic treeは完全走査可能で、chance outcomeもrange vectorへ集約済みです。
  sampling varianceを増やす利点がまだありません。
- Regret-based pruning: rankごとにはprune可能でも、同じpublic branch内にactive rankが残ると
  tree traversal自体は省略できません。正しさを複雑にするため、現在は未実装です。
- node単位の並列化: N=50・7サイズではcheckpoint評価は全体の約3%で、細粒度thread overheadが
  支配的です。N、public node数、反復数がさらに増えた時点で再評価します。
- GPU: 現在は分岐の多いdepth-first traversalが中心で、転送とkernel launchに見合う大きな
  dense batchがありません。

## 再現benchmark

```bash
toy-poker benchmark <config.toml> --iterations 1000 --repeat 3
```

このコマンドはartifactや画像を作らず、kernel＋checkpoint時間、solve全体のwall time、
1 iteration時間、最終ExploitabilityをJSONで出力します。性能変更では、速度だけでなく
`tests/solvers/test_cpp_range.py`によるNumPy版との方策・EV照合を必須とします。

## 参考実装・論文

- [OpenSpiel CFR/CFR+ implementation](https://github.com/google-deepmind/open_spiel/blob/master/open_spiel/algorithms/cfr.h)
- [Discounted Regret Minimization (AAAI 2019)](https://ojs.aaai.org/index.php/AAAI/article/view/4007)
- [Regret-Based Pruning in Extensive-Form Games (NeurIPS 2015)](https://papers.nips.cc/paper_files/paper/2015/hash/c54e7837e0cd0ced286cb5995327d1ab-Abstract.html)
- [postflop-solver](https://github.com/b-inary/postflop-solver) — DCFR、SIMD、混合精度、並列化を採用する公開実装
