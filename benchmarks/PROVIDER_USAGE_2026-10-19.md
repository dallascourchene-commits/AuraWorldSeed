# Provider usage, caching, and deterministic work — October 19, 2026

> **Scope:** User-provided DeepSeek provider CSV exports, not a controlled Aura-vs-no-Aura experiment. The export named `2026-09-20_2026-10-19` contains usage rows only on **September 20, 21, 22, and 24**. **No October activity is recorded in that export.** Absence of rows is not proof of zero use on other carriers. This report preserves these gaps and does not claim a continuous 30-day improvement curve.

## What the exports measure

| Metric | Aug 1–31 export (activity on 8 days, Aug 21–30) | Sept 20–Oct 19 export (activity on 4 days, Sept 20–24) |
| --- | ---: | ---: |
| Requests with provider usage records | 16,233 | 364 |
| Provider input cache-hit tokens | 2,166,235,904 | 187,851,392 |
| Provider input cache-miss tokens | 47,257,546 | 3,032,280 |
| All recorded provider input tokens | 2,213,493,450 | 190,883,672 |
| **Input-token cache-hit share** | **97.8650%** | **98.4115%** |
| Output tokens | 16,295,680 | 518,187 |
| **Actual billed cost (USD)** | **$41.075985** | **$1.593314** |
| Illustrative no-input-cache bill at mapped listed miss rates | $527.75 | $34.50 |
| Illustrative **price** difference versus no-input-cache bill | $486.67 (92.22%) | $32.90 (95.38%) |

The observed cache-hit share is **0.546 percentage points higher** in the later export. Models, prices, volume, traffic patterns, and days are not matched; the shift **cannot be attributed causally** to an Aura upgrade from these exports alone. The large difference in actual total bills also reflects 16,233 versus 364 requests and different provider model families, so it is not a controlled end-to-end savings comparison.

### Observed activity within the requested 30-day export

| Date (provider local day) | Requests | Input cache hits | Input cache misses | Hit share | Actually billed (USD) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09-20 | 57 | 30,768,896 | 526,020 | 98.319% | $0.475438 |
| 2026-09-21 | 139 | 83,922,688 | 1,493,464 | 98.252% | $0.580301 |
| 2026-09-22 | 74 | 60,388,864 | 901,591 | 98.529% | $0.413319 |
| 2026-09-24 | 94 | 12,770,944 | 111,205 | **99.137%** | $0.124256 |

These are four **observed days**, not four consecutive daily checkpoints and not a trend through October 19.

### Earlier August progression (context only)

| Date | Requests | Input cache-hit share | Billed (USD) |
| --- | ---: | ---: | ---: |
| 2026-08-21 | 2,253 | 30.526% | $0.182939 |
| 2026-08-22 | 8 | 0.000% | $0.126703 |
| 2026-08-23 | 56 | 19.085% | $0.588084 |
| 2026-08-26 | 2,844 | 97.807% | $6.626425 |
| 2026-08-27 | 4,635 | 97.858% | $11.679437 |
| 2026-08-28 | 1,224 | 98.374% | $3.331409 |
| 2026-08-29 | 981 | 95.384% | $6.729303 |
| 2026-08-30 | 4,232 | 98.644% | $11.811686 |

The shift from low-cache early August days to high-cache late August days is visible in these records. It is an observed pattern, not a controlled explanation of its causes.

## Mechanism: three different reductions

1. **Zero-call deterministic paths.** Once a task is handled locally by FST/WFST routing, exact mathematics, K27 transforms, rule-based guards, cache lookup, scene/procedural generation, verification, or native CPU computation, that step can execute without an LLM API call. **No count of avoided calls** was provided in the CSVs, so no percentage of request avoidance is asserted here.
2. **Consequence-local source hydration.** When model reasoning is required, Aura's intended workflow sends relevant source/code slices with their dependency, provenance, and currentness roots rather than blindly loading an entire repository. This can reduce context size and support stable shared prefixes. **These exports do not contain prompt/source-slice traces** and therefore do not quantify this mechanism's independent contribution.
3. **Provider-side input caching.** The exports *do* record real input cache-hit and cache-miss token volumes and billed costs. Input caching is a provider pricing/service feature; the architecture may be designed to exploit it, but a controlled intervention would be needed to isolate causal improvement.

**Deterministic call avoidance ≠ context-size reduction ≠ provider cache-hit share ≠ billing savings.** None may be substituted for another.

## Counterfactual method and caveats

**Measured inputs:** `amount-*.csv` contributes `input_cache_hit_tokens`, `input_cache_miss_tokens`, `output_tokens`, and `request_count`; `cost-*.csv` is the authoritative actual USD bill. Duplicated categories within a date are **summed**, never overwritten. API-key/user identifiers are deliberately not published.

`hit_share = hit_tokens / (hit_tokens + miss_tokens)`.

Illustrative no-cache **price** counterfactual keeps output tokens, request count, and observed input-token quantity fixed, then prices each cache-hit tier at its paired listed miss-input tariff, leaving actual miss and output charges unchanged:

- Sept `deepseek-flash`: hit-price tiers $0.000000003 and $0.000000006/token mapped to miss-price tiers $0.00000015 and $0.00000030/token, respectively (50×).
- August `deepseek-v4-flash`: hit-price tiers $0.000000007 and $0.000000014/token mapped to miss-price tiers $0.00000022 and $0.00000044/token (220/7×).
- August `deepseek-v4-pro`: cache-hit price $0.000000022/token mapped to standard miss price $0.00000066/token (30×); other rate tiers and billing arrangements may alter a true hypothetical bill.

Formula: `counterfactual = actual_provider_cost - billed_hit_input_cost + sum(hit_tokens_at_tier × mapped_miss_price_at_tier)`.

This is **not** a prediction of a real invoice if cache were disabled: requests, prompt prefixes, model selection, pricing tiers, and customer behavior could all change. The figure is not an energy, wall-time, or total tokens saved measurement. A model may still need to process cached information in ways not visible in these exports.

For a causal Aura benchmark, freeze the task corpus and model/tariffs, measure identical output quality, compare whole-repository versus surgical-slice context, deterministic routing enabled/disabled, cold/warm caches, all external calls, wall time, and total billed cost, and retain item-level receipts.

## Related materials

- [README benchmark standing](../README.md)
- [Executable benchmark ledger](README.md)
- [Origin Story: Anishinaabemowin and consequence-local computing](../docs/ORIGIN_STORY.md)
- [Paper X Rev.3](https://doi.org/10.5281/zenodo.22134815)
- [Paper XI Rev.2](https://doi.org/10.5281/zenodo.23204234)

Source status: private user-provided zipped provider exports (August 1–31 and September 20–October 19, 2026), audited October 19, 2026. Raw exports are **not** committed because they contain account/key metadata. This publication includes only aggregated, non-secret values.
