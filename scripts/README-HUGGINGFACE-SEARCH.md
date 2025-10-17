# HuggingFace Resource Search

## Overview

This script systematically searches HuggingFace for models and datasets relevant to Home Assistant pattern detection.

## Installation

```bash
pip install -r scripts/requirements-search.txt
```

Or install directly:
```bash
pip install huggingface_hub
```

## Usage

### Run Complete Search

```bash
python scripts/search-huggingface-resources.py
```

This will:
1. Search 15+ categories (time series, energy, IoT, smart home, etc.)
2. Save JSON results to `docs/kb/huggingface-research/`
3. Generate summary report with top findings
4. Provide recommendations for integration

### Output Files

**Location:** `docs/kb/huggingface-research/`

- `SEARCH_SUMMARY.md` - Human-readable summary with top 5 in each category
- `all_results.json` - Combined results (all categories)
- `time_series_models.json` - Time series forecasting models
- `energy_models.json` - Energy consumption models
- `smart_home_datasets.json` - Smart home datasets
- `home_assistant_datasets.json` - HA-specific datasets
- `iot_models.json` - IoT sensor models
- `anomaly_models.json` - Anomaly detection models
- ... and more category-specific files

## Search Categories

### Models

1. **Time Series** (Highest Priority)
   - Time series forecasting models
   - Temporal pattern models
   
2. **Energy & Smart Home** (High Priority)
   - Energy consumption models
   - Smart meter models
   - Appliance recognition (NILM)

3. **IoT** (Medium Priority)
   - IoT sensor models
   - Sensor anomaly detection

4. **Home Assistant** (Low Probability)
   - HA-specific models (if any exist)

5. **Anomaly Detection** (Medium Priority)
   - General anomaly detection models

### Datasets

1. **Smart Home** (Highest Priority)
   - Smart home datasets
   - Home automation datasets
   - User behavior/routine datasets

2. **Energy** (High Priority)
   - Energy consumption datasets
   - Smart meter data
   - Appliance usage (NILM)

3. **IoT** (Medium Priority)
   - IoT sensor datasets
   - Device event datasets

4. **Time Series** (Medium Priority)
   - General time series datasets

## Evaluation Criteria

When reviewing results, consider:

### For Models
- ✅ Training data domain (consumer vs industrial IoT)
- ✅ Accuracy benchmarks (need >75% for consideration)
- ✅ Inference speed (<500ms preferred)
- ✅ Model size (<2GB for local deployment)
- ✅ Last updated (prefer <6 months old)
- ✅ Downloads/likes (indicates quality/popularity)
- ✅ Documentation quality

### For Datasets
- ✅ Size (prefer >10K samples)
- ✅ Data format (time series with timestamps)
- ✅ Labels/annotations (device types, states)
- ✅ Privacy/license (must be open/commercial use OK)
- ✅ Domain match (consumer smart home > industrial IoT)

## Expected Findings

Based on research and web search:

### High Probability (>70%)
- ✅ General time series models
- ✅ Energy consumption forecasting models
- ✅ Smart grid/utility models
- ✅ Generic sensor anomaly detection

### Medium Probability (30-50%)
- ⚠️ NILM/appliance disaggregation models
- ⚠️ Smart home energy datasets
- ⚠️ IoT event sequence models
- ⚠️ User behavior/routine datasets (EdgeWisePersona type)

### Low Probability (<20%)
- ❌ Home Assistant specific models
- ❌ Smart home automation pattern datasets
- ❌ Consumer IoT pattern recognition models

## Next Steps After Search

1. **Review Summary**
   - Open `docs/kb/huggingface-research/SEARCH_SUMMARY.md`
   - Review top 5 results in each category

2. **Deep Dive Top Candidates**
   - Visit HuggingFace pages for promising models/datasets
   - Read model cards and documentation
   - Check accuracy benchmarks
   - Review example code

3. **Test on Sample Data**
   - Download top 3 models
   - Test on sample HA event data
   - Measure accuracy vs rule-based (85-90% baseline)
   - Measure inference speed

4. **Make Integration Decision**
   ```python
   if specialized_model_accuracy > rule_based_accuracy + 10%:
       integrate = True
       reason = "Significant improvement justifies complexity"
   elif specialized_model_accuracy > rule_based_accuracy + 5%:
       integrate = "Consider"
       reason = "Marginal improvement, evaluate maintenance cost"
   else:
       integrate = False
       reason = "Stick with rules - simpler and comparable accuracy"
   ```

5. **Document Findings**
   - Update Context7 KB with actual model names
   - Note accuracy benchmarks
   - Record integration decisions

## Custom Searches

You can modify the script to add custom searches:

```python
# Add to searches dictionary in main()
searches = {
    "custom_search": {
        "query": "your search terms OR other terms",
        "kind": "model",  # or "dataset"
        "limit": 30
    }
}
```

### Search Query Syntax

- `OR` - Logical OR (find any match)
- `AND` - Logical AND (find all matches)
- `pipeline_tag:X` - Filter by pipeline type
- `"exact phrase"` - Exact phrase match

Examples:
```python
"pipeline_tag:time-series-forecasting"           # All time series models
"home assistant OR homeassistant"                # Either spelling
"energy AND consumption"                         # Both terms required
"smart home AND NOT video"                       # Exclude video
```

## Troubleshooting

### Import Error
```
ERROR: huggingface_hub not installed
```
**Solution:** `pip install huggingface_hub`

### API Rate Limiting
If you hit rate limits, the script will handle gracefully and return partial results.

### No Results
If a category returns no results, it means HuggingFace has no matching content in that area.

## Integration with Pattern Detection

### If You Find Good Models

**Recommended Integration Path:**

1. **Phase 1: MVP (Use Rules)**
   - Build rule-based detectors (85-90% accuracy)
   - Deploy quickly
   - Proven approach

2. **Phase 2: Test Specialized Models**
   - Download top candidates from search
   - Test on your HA data
   - Benchmark accuracy

3. **Phase 3: Integrate if Better**
   - If specialized model > 90% accuracy
   - Integrate as optional detector
   - Keep rules as fallback

### Known Good Datasets (From Web Research)

If search finds these, prioritize them:

1. **EdgeWisePersona** - User routine detection (VERY HIGH VALUE)
2. **Hermes FC Cleaned** - HA integration examples (HIGH VALUE)
3. **SmartHome-Bench** - Anomaly detection (HIGH VALUE)
4. **IoT QA Chat** - Device understanding (MEDIUM VALUE)

## Reference

- HuggingFace Hub API Docs: https://huggingface.co/docs/huggingface_hub
- Search syntax: https://huggingface.co/docs/hub/search
- Model cards: https://huggingface.co/docs/hub/model-cards

## Questions?

Review the main knowledge base entry for detailed evaluation criteria and integration strategy.

