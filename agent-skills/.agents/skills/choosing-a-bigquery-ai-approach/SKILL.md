---
name: choosing-a-bigquery-ai-approach
description: Use FIRST when someone wants to predict, classify, forecast, embed/search, or explain something in BigQuery but hasn't said whether they want a trained model (BigQuery ML) or a generative AI function call (BigQuery AI Functions/Gemini-in-SQL) — or when it's genuinely unclear which fits better. Triages between the sibling bigquery-ml and bigquery-ai-functions skills and asks a clarifying question when the answer isn't obvious, rather than guessing.
---

# Choosing a BigQuery AI Approach

BigQuery has two distinct ways to add intelligence to SQL, and they are not interchangeable:

- **BigQuery ML** (`CREATE MODEL` + `ML.*`) — trains a model on your labeled/historical data. See the `bigquery-ml` skill.
- **BigQuery AI Functions** (`AI.*`, Gemini-in-SQL) — calls a foundation model per-row or per-call, zero training. See the `bigquery-ai-functions` skill.

Both can be reached via `CREATE MODEL` + `ML.*` (structured, trained) or `AI.*` (generative, zero-setup) — the right choice depends on the shape of the problem, not the task category. This skill exists to make that call *before* diving into either domain skill's own catalog, and to ask rather than guess when it's genuinely ambiguous.

## Ask yourself (or the user) these questions first

1. **Do you have labeled historical data, and do you want a model that gets better as that data grows, retrained on a schedule?**
   Yes → lean BigQuery ML. No / one-off → lean BigQuery AI Functions.
2. **Do you need coefficient-level interpretability, feature importance, or a formal audit trail for a regulated decision?**
   Yes → BigQuery ML (`ML.WEIGHTS`, `ML.GLOBAL_EXPLAIN`, `ML.FEATURE_IMPORTANCE`). Generative functions don't expose this.
3. **Is the task naturally expressed as a prompt/instruction** ("is this spam?", "summarize this", "extract these fields", "rate this 1-10") **rather than a numeric feature table?**
   Yes → BigQuery AI Functions. The managed functions (`AI.IF`/`AI.SCORE`/`AI.CLASSIFY`/`AI.AGG`) and generation functions are built exactly for this.
4. **For a regression or classification on a normal feature table, do you need reproducible predictions, >20 feature columns, or >10 classes?**
   Yes → a trained model (`LINEAR_REG`, `LOGISTIC_REG`, `BOOSTED_TREE_*` — BigQuery ML). No, and you'd rather skip training entirely → `AI.PREDICT` (TabFM, zero training). Note that **tabular prediction is no longer BigQuery ML's exclusively** — `AI.PREDICT` is a foundation model for ordinary feature tables, so "it's tabular" is not by itself a reason to route to BigQuery ML.
5. **For a time series, are you predicting the future or describing the past?** Three answers, not two. Predicting, and you need custom holidays, external regressors, hierarchical reconciliation, or explicit forecast-bound control → `ARIMA_PLUS`/`ARIMA_PLUS_XREG` (BigQuery ML). Predicting, and you just want a fast baseline → `AI.FORECAST` (zero training, BigQuery AI Functions). **Describing** — you want the trend, the seasonal components, or the points where the level shifted, and no forecast at all → `ML.TREND` / `ML.SEASONALITY` / `ML.DETECT_CHANGE_POINTS` (BigQuery ML, model-free TVFs, no `CREATE MODEL`).
7. **Do you need >12 dimensions, or a ratio/category metric type, for a "why did this metric move" analysis?**
   Yes → `CONTRIBUTION_ANALYSIS` (BigQuery ML). No, ≤12 dimensions and a summable metric → `AI.KEY_DRIVERS` (zero training, faster).
8. **Is this unstructured content** (free text, images, documents) **that needs semantic understanding, generation, or search?**
   Yes → BigQuery AI Functions (`AI.GENERATE*`, `AI.EMBED`, `VECTOR_SEARCH`, `AI.CLASSIFY`). BigQuery ML's models are structured/tabular-first (though PCA/AUTOENCODER can embed structured data, and `embeddings_classification` shows the two approaches composing).
9. **Do you need this to run at real production scale with monitoring, drift detection, and a scheduled retrain pipeline?**
   Yes → BigQuery ML has the full lifecycle for this (`ML.VALIDATE_DATA_DRIFT`, 8 orchestration pipeline approaches). Generative functions are typically called per-request rather than "retrained."

If two or more answers point the same direction, that's your answer — go to that skill's decision tree. **If the answers conflict or the task doesn't map cleanly onto any of these questions, ask the user directly** which of the tradeoffs above matters most to them, with 2-3 concrete options and the tradeoff for each — don't silently pick one.

## Worked head-to-head comparisons (already resolved in this project)

These pairs solve visibly similar problems with the two different approaches, and both sides have been built and tested — use them as calibration examples:

- **Forecasting**: `ARIMA_PLUS` (BigQuery ML) vs. `AI.FORECAST` (BigQuery AI Functions). `AI.FORECAST` is faster to stand up (no `CREATE MODEL`) but has no custom holidays, no external regressors, no hierarchy, and less control over forecast bounds. `ARIMA_PLUS`/`ARIMA_PLUS_XREG` trade setup time for that control.
- **Time series decomposition — model vs. model-free**: `ARIMA_PLUS`'s `ML.EXPLAIN_FORECAST` (BigQuery ML, needs a trained model) vs. `ML.TREND`/`ML.SEASONALITY` (BigQuery ML, TVFs straight over a table). Both were run on the same Citi Bike series: `ML.SEASONALITY`'s weekly and yearly components come back **bit-identical** to the model's `seasonal_period_*` output (mean abs diff 0.0, corr 1.0), so if seasonality is all you want, the model buys you nothing. `ML.TREND` is close but not identical (corr 0.9955) — and it defaults `adjust_step_changes` to FALSE where the model defaults it TRUE, so the two disagree out of the box.
- **Change points vs. anomalies vs. drift** — three different questions that all sound like "something changed": `ML.DETECT_CHANGE_POINTS` finds *windows where the level shifted and stayed shifted*; `ML.DETECT_ANOMALIES`/`AI.DETECT_ANOMALIES` find *individual off-baseline rows*; `ML.VALIDATE_DATA_DRIFT` compares *whole datasets*. On the tested series the first two overlap zero. **Before acting on any change point, profile the series for data gaps** — all three decomposition TVFs gap-fill first, so an ingestion outage produces a textbook structural break that is not a real one. On the tested table, six of seven detected change points were gap edges.
- **Driver / key-factor analysis**: `CONTRIBUTION_ANALYSIS` (BigQuery ML) vs. `AI.KEY_DRIVERS` (BigQuery AI Functions). `AI.KEY_DRIVERS` is simpler and zero-training but caps at 12 dimensions and summable metrics only; `CONTRIBUTION_ANALYSIS` supports more dimensions and ratio/category metric types.
- **Tabular regression / classification**: a trained model (`LINEAR_REG`, `LOGISTIC_REG`, `BOOSTED_TREE_*` — BigQuery ML) vs. `AI.PREDICT` (TabFM — BigQuery AI Functions). `AI.PREDICT` needs no `CREATE MODEL` and no labeled training run, but it caps at **20 feature columns and 10 classes**, and — measured, not documented — **its output is not deterministic**: repeating a byte-identical call returns slightly different predictions, and `FARM_FINGERPRINT` pins only *which rows* split, never the predictions themselves. `AI.EVALUATE` scores its own fresh predictions rather than any rows you materialized. If a number has to reproduce, train the model.
- **Classification (unstructured / prompt-shaped input)**: a trained classifier (`BOOSTED_TREE_CLASSIFIER`, `LOGISTIC_REG`, etc. — BigQuery ML) needs labeled training data and improves with volume/retraining, but is fast and cheap per-prediction once trained. `AI.CLASSIFY` (BigQuery AI Functions) needs zero training data — just a category list — but costs an LLM call per row and won't out-learn a well-trained model's precision on a stable, high-volume task.
- **Embeddings**: BigQuery ML's `PCA`/`AUTOENCODER`/`MATRIX_FACTORIZATION` models can produce embeddings from structured/tabular data via `ML.GENERATE_EMBEDDING`. BigQuery AI Functions' `AI.EMBED`/`AI.GENERATE_EMBEDDING` produce embeddings from text/image/multimodal content via a foundation model. These aren't really competing — pick by input type (tabular vs. unstructured content).
- **The two approaches compose, they aren't always exclusive** — `bq-ml`'s `embeddings_classification` workflow uses `AI.EMBED` (generative) to featurize product names, then a trained `BOOSTED_TREE_CLASSIFIER` (BigQuery ML) to classify with those embeddings as input. Don't assume the answer is always either/or.

## After triaging

Route to the matching skill for the actual decision tree and implementation detail:
- Trained models, model management, reproducible tabular prediction, or scheduled pipelines → [`bigquery-ml` skill](../bigquery-ml/SKILL.md).
- Generative/prompt-driven tasks, embeddings/search over unstructured content, zero-training tabular prediction/forecasting/anomalies/drivers, or document processing → [`bigquery-ai-functions` skill](../bigquery-ai-functions/SKILL.md).

This skill only triages — it deliberately does not duplicate either domain skill's own catalog or gotchas.
