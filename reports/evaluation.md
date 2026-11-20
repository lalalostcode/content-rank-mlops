# Synthetic model selection and holdout evaluation

## Protocol

The fixture was generated with seed `20261120` at cutoff `2025-02-01T00:00:00Z`. Evaluation uses `trend_direction == "down"` on the eligible inventory. A seeded draw (`42`) reserved four of the 16 eligible clients before fitting. Five `GroupKFold` splits on the other clients produced one out-of-fold score per eligible development item. The two clients with no eligible rows remained in the development coverage counts. [Snapshot contract](../docs/data-dictionary.md) · [GroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupKFold.html)

- The rule weights are 40% visibility, 30% freshness, 25% position opportunity and 5% depth gap. Percentiles and position scaling use eligible items in each client. Missing evidence contributes zero for its rule component.
- Base and engineered LambdaRank use the same fixed CPU recipe. Each fold fits its own categorical vocabulary on training clients. Numeric nulls go to LightGBM, and categorical nulls and unseen values have separate indicators. Training rows are contiguous by client query. [LightGBM parameters](https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html)
- The blend gives each model half the weight and uses ascending average ranks divided by eligible count within each client. For all four methods, equal final scores sort by content ID. Precision uses `min(K, eligible count)` as denominator. Binary NDCG uses the same cutoff and is zero for a client with no positives. Both metrics weight included clients equally.

## Development and selection

| Method | P@10 | P@25 | P@50 | NDCG@10 | NDCG@25 | NDCG@50 |
|---|---:|---:|---:|---:|---:|---:|
| Fixed rule | 0.4333 | 0.4303 | 0.4370 | 0.4621 | 0.5276 | 0.6159 |
| Base LambdaRank | 0.9250 | 0.7936 | 0.6237 | 0.9778 | 0.9775 | 0.9727 |
| Engineered LambdaRank | 0.9250 | 0.7903 | **0.6270** | 0.9720 | 0.9721 | 0.9715 |
| Equal blend | 0.9250 | 0.7936 | 0.6254 | 0.9757 | 0.9766 | 0.9728 |

Development covered 816 eligible items across 12 clients. Two other clients had no eligible items. Zero included clients had no positives. The numbers of included clients below K were 0, 2 and 5 for K of 10, 25 and 50, respectively.

The frozen criteria required positive macro P@50 lift over the rule, both label values in each evaluated cohort and no client losing more than 10 percentage points of P@50. Among qualifying methods, selection used macro P@50, then NDCG@50, then the simpler strategy. The engineered model led at the primary cutoff by 19.0 percentage points over the rule. Both components were refit using only development clients and exported with the selection decision. A separate command verified that frozen manifest and the exact input before evaluating the chosen strategy and rule on the holdout. [Selection code](../pipeline/training/selection.py) · [Training and final evaluation](../pipeline/training/run.py)

## Final holdout

| Method | P@10 | P@25 | P@50 | NDCG@10 | NDCG@25 | NDCG@50 |
|---|---:|---:|---:|---:|---:|---:|
| Fixed rule | 0.2750 | 0.4000 | 0.3700 | 0.2978 | 0.3986 | 0.5239 |
| Frozen engineered LambdaRank | 0.7500 | 0.6500 | **0.4400** | 0.7500 | 0.7097 | 0.7401 |

The holdout covered 180 eligible items across four clients. One client was below all three K values and had zero positives. No client was empty or lost P@50 relative to the rule. All frozen checks passed. The final manifest selects the engineered ranker for synthetic local scoring. The rule remains the fallback when a frozen candidate fails a gate.

`development.json` and `final-evaluation.json` in local evidence contain every client's precision, binary NDCG, effective K, nonrelevant items in the queue, positive items below the queue and differences from the rule. Two development runs agreed byte-for-byte on the split, development report, bundle and frozen manifest. The holdout benchmark was run after that comparison. See the [execution report](../docs/reports/CYCLE_01_EXECUTION_REPORT.md) for local paths and evidence digests.

The generated fixture contains an invented association between engagement and decline to exercise learning and model selection. This experiment measures observed-decline ranking on that fixture. Four final clients limit precision estimates, and undersized queues have the same P@K for any full-inventory ordering. The capstone's historical 92.4% came from averaging pooled fold-level P@50 on the FlyRank starter cohort. An approved independent cohort and owner review are still needed for real-data model acceptance. [Capstone report](https://github.com/lalalostcode/FlyrankAI_ML/blob/main/work/capstone_report.md) · [Phase 3 protocol](../docs/phases/PHASE_03_MACHINE_LEARNING.md#evaluation-protocol)
