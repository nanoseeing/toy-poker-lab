# Public strategy studies

教材で参照する固定済みsolver runです。理論と解説は[`docs/studies`](../../docs/studies/README.md)を参照してください。

| Study | Report | Viewer | Exploitability |
|---|---|---|---:|
| `akq_k_vs_aq_allin` | [Report](akq_k_vs_aq_allin/report.md) | [Viewer](akq_k_vs_aq_allin/strategy_viewer.html) | `0` |
| `akq_k_vs_aq_variable_size` | [Report](akq_k_vs_aq_variable_size/report.md) | [Viewer](akq_k_vs_aq_variable_size/strategy_viewer.html) | `2.3830116e-06` |
| `akq_symmetric_allin` | [Report](akq_symmetric_allin/report.md) | [Viewer](akq_symmetric_allin/strategy_viewer.html) | `4.0376354e-06` |
| `akq_symmetric_ip_betting` | [Report](akq_symmetric_ip_betting/report.md) | [Viewer](akq_symmetric_ip_betting/strategy_viewer.html) | `5.0386425e-06` |
| `akq_symmetric_two_street` | [Report](akq_symmetric_two_street/report.md) | [Viewer](akq_symmetric_two_street/strategy_viewer.html) | `5.8007352e-06` |
| `akq_symmetric_variable_size` | [Report](akq_symmetric_variable_size/report.md) | [Viewer](akq_symmetric_variable_size/strategy_viewer.html) | `7.4617445e-06` |
| `akqj_two_street_pot` | [Report](akqj_two_street_pot/report.md) | — | `3.5914e-06` |
| `akqj_two_street_variable_size` | [Report](akqj_two_street_variable_size/report.md) | [Viewer](akqj_two_street_variable_size/strategy_viewer.html) | `3.692386e-06` |
| `zero_one_n50_one_street` | [Report](zero_one_n50_one_street/report.md) | [Viewer](zero_one_n50_one_street/strategy_viewer.html) | `1.6662251e-08` |
| `zero_one_n50_two_street` | [Report](zero_one_n50_two_street/report.md) | [Viewer](zero_one_n50_two_street/strategy_viewer.html) | `5.8126218e-06` |

再生成:

```bash
toy-poker publish-studies --selection configs/public_studies.toml
```
