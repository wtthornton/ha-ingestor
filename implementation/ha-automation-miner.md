# Home Assistant Automation Miner — Cursor.ai Spec

> **Goal**: Build a repeatable data-mining pipeline that discovers Home Assistant automation *ideas* (not raw YAML), normalizes them into structured metadata, and stores them in **SQLite** for use by an AI assistant that generates device-specific YAML on demand.

---

## 0) Scope & Outcomes

**You will implement** (Cursor will write code):
- A crawler for **Discourse (Home Assistant Blueprints Exchange)** and **GitHub blueprint libraries**.
- A parser that extracts **intent-level metadata** from posts/READMEs and embedded blueprint YAML.
- A normalizer that maps inputs to a **capability taxonomy** (triggers, conditions, actions, device classes).
- A **SQLite** persistence layer with indexes + de-duplication + scoring.
- A small **CLI** and **Python SDK** to query the corpus by the user’s devices/integrations.
- A set of **prompt templates** to drive YAML generation from metadata (device-aware).

**You will not** store full YAML for re-use; you’ll store *ideas + structure* to synthesize YAML later.

---

## 1) Data Sources (minimally required)

1. **Home Assistant Community — Blueprints Exchange (Discourse)**
   - Category index (JSON): `https://community.home-assistant.io/c/blueprints-exchange/53.json`
   - Topic JSON: `https://community.home-assistant.io/t/<slug>/<topic_id>.json`
   - What to extract:
     - title, slug, topic_id, created_at, last_posted_at, tags, like_count, reply_count, views
     - first post **raw** body (Markdown/HTML -> text)
     - embedded blueprint code blocks (look for ```yaml + `blueprint:` key)
     - external links (GitHub repo links, gists, import links)
   - Notes: Respect robots.txt & rate limiting; pagination via `page=` on category; use `more_topics_url` from JSON when present.

2. **GitHub — Blueprint Libraries & Awesome Lists**
   - Seed repos: discovered via Awesome lists and topic search:
     - Topic search: `topic:home-assistant-blueprint` `language:YAML` `"blueprint:"` `path:blueprints`
   - API endpoints (unauthenticated is limited; use token if available):
     - Code search: `GET https://api.github.com/search/code?q=<query>&per_page=100&page=1`
     - Repo contents: `GET https://api.github.com/repos/{owner}/{repo}/contents`
     - Repo metadata: `GET https://api.github.com/repos/{owner}/{repo}`
   - What to extract:
     - file paths, raw YAML, README text, stars/forks/watchers, default branch, last commit date
     - license (from repo), author/owner
   - Notes: Cache raw files locally; store etags; respect secondary rate limits.

> Optional extensions: Cookbook threads, “Automations from Zero to Hero”, Node-RED flow mega-threads (map flows → HA intent patterns).

---

## 2) Repository Layout

```
ha-automation-miner/
  README.md
  .env.example
  data/
    cache/
    sqlite/
      automations.db
  src/
    config.py
    utils/
      http.py
      text.py
      yaml_tools.py
      scoring.py
      dedupe.py
      nlp.py
    crawlers/
      discourse.py
      github.py
    parsers/
      discourse_post.py
      github_repo.py
    normalizers/
      taxonomy.py
      blueprint_to_capabilities.py
    store/
      db.py
      ddl.sql
      queries.py
    cli.py
    sdk.py
  tests/
    test_parsing.py
    test_normalize.py
    test_store.py
```

---

## 3) Environment & Setup

Create **.env**:
```
GITHUB_TOKEN=ghp_xxx            # optional but recommended
USER_AGENT=ha-automation-miner/1.0 (+https://example.local)
DISCOURSE_BASE=https://community.home-assistant.io
DB_PATH=./data/sqlite/automations.db
CACHE_DIR=./data/cache
```

Install:
```
python -m venv .venv && source .venv/bin/activate
pip install httpx pydantic pyyaml beautifulsoup4 markdown-it-py rapidfuzz python-slugify sqlite-utils tiktoken
```

---

## 4) SQLite Schema (DDL)

```sql
-- src/store/ddl.sql

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN ('discourse','github','other')),
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  author TEXT,
  license TEXT,
  stars INTEGER DEFAULT 0,
  forks INTEGER DEFAULT 0,
  watchers INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  replies INTEGER DEFAULT 0,
  views INTEGER DEFAULT 0,
  created_at TEXT,
  updated_at TEXT,
  last_crawled_at TEXT
);

CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL REFERENCES sources(id),
  external_id TEXT,              -- topic_id, repo_path, file_sha, etc.
  slug TEXT,
  title TEXT NOT NULL,
  summary TEXT,
  raw_text TEXT,                 -- normalized text (no HTML)
  raw_yaml TEXT,                 -- blueprint YAML if present (for parsing only, optional)
  url TEXT,
  created_at TEXT,
  updated_at TEXT,
  like_count INTEGER DEFAULT 0,
  reply_count INTEGER DEFAULT 0,
  view_count INTEGER DEFAULT 0,
  stars INTEGER DEFAULT 0,
  forks INTEGER DEFAULT 0,
  watchers INTEGER DEFAULT 0,
  license TEXT,
  quality_score REAL DEFAULT 0.0,
  hash TEXT,                     -- content hash for dedupe
  UNIQUE(source_id, external_id)
);

CREATE TABLE IF NOT EXISTS capabilities (
  id INTEGER PRIMARY KEY,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  -- intent-level metadata
  use_case TEXT,                 -- e.g., "motion_lighting", "presence_simulation"
  triggers TEXT,                 -- JSON array of normalized trigger tokens
  conditions TEXT,               -- JSON array of normalized condition tokens
  actions TEXT,                  -- JSON array of normalized action tokens
  entities TEXT,                 -- JSON array of {domain, device_class?}
  integrations TEXT,             -- JSON array of integration names (e.g., ["zha","mqtt","hue"])
  brands TEXT,                   -- JSON array of brand hints (["Aqara","Zooz","Shelly"])
  complexity TEXT,               -- low | medium | high
  tags TEXT,                     -- JSON array of arbitrary tags
  score REAL DEFAULT 0.0
);

CREATE TABLE IF NOT EXISTS links (
  id INTEGER PRIMARY KEY,
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  kind TEXT,                     -- "github", "import", "doc", "image", etc.
  url TEXT
);

CREATE INDEX IF NOT EXISTS idx_items_quality ON items(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_caps_usecase ON capabilities(use_case);
CREATE INDEX IF NOT EXISTS idx_caps_integrations ON capabilities(integrations);
CREATE INDEX IF NOT EXISTS idx_caps_entities ON capabilities(entities);
CREATE INDEX IF NOT EXISTS idx_items_hash ON items(hash);
```

---

## 5) Normalization Taxonomy

> Keep tokens compact and model-friendly. Prefer finite vocabularies for joins and ranking.

**Entity Domains**: `binary_sensor`, `sensor`, `light`, `switch`, `cover`, `climate`, `media_player`, `lock`, `alarm_control_panel`, `button`, `scene`, `input_boolean`, `input_number`

**Device Classes (examples)**:
- binary_sensor: `motion`, `occupancy`, `door`, `window`, `presence`, `smoke`, `moisture`
- sensor: `illuminance`, `temperature`, `humidity`, `power`, `co2`

**Triggers**: `motion_detected`, `occupancy`, `door_open`, `window_open`, `state_change`, `sunrise`, `sunset`, `time_range`, `schedule`, `webhook`, `mqtt_event`, `button_single`, `button_double`, `scene_activated`

**Conditions**: `night_time`, `illuminance_below`, `nobody_home`, `somebody_home`, `weekend`, `quiet_hours`, `climate_mode`, `power_price_high`, `weather_condition`

**Actions**: `turn_on_light`, `turn_off_light`, `set_brightness`, `set_color_temp`, `notify_mobile`, `play_tts`, `set_scene`, `start_timer`, `delay`, `set_climate_mode`, `open_cover`, `lock_door`

**Use Cases (starter set)**:
- `motion_lighting`, `presence_lighting`, `nightlight`, `vacation_presence`, `energy_saver`, `media_pausing`, `door_alert`, `leak_alert`, `garage_guard`, `pet_mode`, `wake_routine`, `sleep_routine`

---

## 6) Crawlers

### 6.1 Discourse Crawler (`src/crawlers/discourse.py`)
- Inputs: `DISCOURSE_BASE`, category id = `53` (Blueprints Exchange), pagination
- Steps:
  1. Fetch category JSON → list topics. Respect `more_topics_url`.
  2. For each topic: fetch `/t/<slug>/<topic_id>.json`
  3. Extract:
     - metadata: title, tags, like/reply/view counts, created/updated, author
     - **post raw** (markdown) and **links**
     - code blocks marked as YAML; if contains `blueprint:` capture in `raw_yaml`
  4. Persist to `sources` + `items` + `links`.
  5. Compute `hash` of `(title + raw_text + raw_yaml?)` for dedupe.

- Rate limit: add random sleep 0.5–1.5s; support resume checkpoints.

### 6.2 GitHub Crawler (`src/crawlers/github.py`)
- Inputs: `GITHUB_TOKEN` (optional), seed queries
- Steps:
  1. Code search queries:  
     - `q=topic:home-assistant-blueprint language:YAML "blueprint:"`
     - `q="blueprint:" language:YAML path:blueprints`
  2. For each match: fetch raw file, detect blueprint YAML.
  3. Fetch repo metadata (stars, forks, license). Extract README.
  4. Persist to `sources` (per repo) and `items` (per file).
  5. Compute `hash` for dedupe.

- Caching: store `etag` and `last-modified`. Retry with backoff on 403.

---

## 7) Parsers & Capability Extraction

### 7.1 YAML Heuristics
- A file/post is considered a blueprint candidate if:
  - It has a YAML code block with `blueprint:` root key, or
  - It links to a raw YAML containing `blueprint:`.

- Extract from YAML (when present) **for capability hints only**:
  - `input:` → derive **entities required** (`selector` types: `entity`, `device`, `number`, `boolean`).
  - Service calls under `action:` → map to **actions** (e.g., `light.turn_on` → `turn_on_light`).
  - Triggers → map to normalized triggers (`platform: state`, entity domain → token).
  - Conditions → map to normalized conditions.
  - **Do not** store or re-distribute full YAML beyond transient parsing.

### 7.2 Text Mining (post body / README)
- Regex/NLP to detect:
  - **Integrations**: `zha`, `zwave_js`, `zigbee2mqtt`, `mqtt`, `esphome`, `hue`, `shelly`, `tplink`, `unifi`, `plex`
  - **Brands**: `Aqara`, `Zooz`, `Shelly`, `Philips Hue`, `Tuya`, `Govee`
  - **Device classes**: `motion`, `occupancy`, `illuminance`, etc.
  - **Use-case keywords** mapped to `use_case` taxonomy
- Keep a stoplist to avoid false positives (“hue” vs “hue of a color”).

### 7.3 Complexity Scoring
- `low`: 1–2 triggers, 0–1 conditions, 1–2 actions
- `medium`: >2 triggers or >2 conditions
- `high`: multiple domains + timers + scenes + templating mention

---

## 8) De-duplication & Quality Scoring

### 8.1 Dedupe
- `hash = sha256(normalize(title) + normalize(raw_text) + normalized capability tokens)`
- Near-duplicate detection via `rapidfuzz` on titles + summaries (threshold 90)

### 8.2 Quality Score (0–1)
```
quality = sigmoid(
    0.6 * log1p(likes + replies + views/100)
  + 0.4 * log1p(stars + forks + watchers)
) * recency_decay(days_since_update)
```
- `recency_decay(d) = exp(-d / 365)`

Store into `items.quality_score` and `capabilities.score`.

---

## 9) CLI & SDK

### CLI (`src/cli.py`)
```
# Crawl
python -m src.cli crawl --source discourse --pages 5
python -m src.cli crawl --source github --query 'topic:home-assistant-blueprint'

# Normalize existing items to capabilities
python -m src.cli normalize --limit 1000

# Query by user devices/integrations
python -m src.cli suggest --devices '["binary_sensor.motion","light"]' --integrations '["zha","hue"]' --top 20

# Export for LLM
python -m src.cli export --format jsonl --out ./data/corpus.jsonl --min_quality 0.4
```

### SDK (`src/sdk.py`)
```python
from src.sdk import suggest_automations

suggestions = suggest_automations(
    devices=["binary_sensor.motion","light.dimmable"],
    integrations=["zha","hue"],
    goals=["energy_saver","nightlight"],
    topk=20
)
```

---

## 10) Query Logic (Fit Ranking)

Given user graph `{devices, integrations, goals}`:
1. Compute **entity fit**: overlap of required entity domains/classes with user devices.
2. Compute **integration fit**: overlap with user integrations.
3. Optional **goal boost**: match `use_case` to user goals.
4. Final score: `fit_score * quality_score`

`fit_score = 0.6*entity_jaccard + 0.4*integration_jaccard`

---

## 11) Prompt Templates (for YAML Synthesis)

> Store these in `prompt_templates.md`. Cursor will substitute variables.

**A) Suggestion Prompt**
```
SYSTEM:
You generate Home Assistant automation ideas. You have a corpus of normalized automation metadata.

USER DEVICES: {{devices_json}}
USER INTEGRATIONS: {{integrations_json}}
USER GOALS: {{goals_json}}

TASK:
Return the top {{k}} automation ideas. For each, include:
- title
- why it fits (entities, integrations)
- steps (triggers, conditions, actions) at intent level
- any missing device suggestions (brands allowed: generic)
```

**B) YAML Generation Prompt**
```
SYSTEM:
You write Home Assistant YAML automations from intent metadata.

CONTEXT (METADATA):
{{metadata_json}}

USER DEVICES/ENTITIES:
{{user_entities_json}}

REQUIREMENTS:
- Use only entities/integrations available to the user.
- If a required capability is missing, propose a device to buy and STOP without generating YAML.
- If everything exists, output a single YAML automation with best practices (ids, aliases, comments).
```

**C) Explainer Prompt**
```
SYSTEM:
Explain the automation concept to a non-expert.

METADATA:
{{metadata_json}}

TASK:
Describe what it does, why it’s useful, and how to test it.
```

---

## 12) Tests

- **Parsing**: fixture posts with YAML codeblocks → expected `capabilities` rows.
- **Normalization**: YAML → triggers/conditions/actions tokens mapped correctly.
- **Dedupe**: near-identical titles collapse to single canonical item.
- **Scoring**: higher likes/stars and recent items rank higher.
- **Suggest**: given mock user graph, top results contain required domains.

---

## 13) Operational Notes

- **Rate limits**: add exponential backoff; persist cursors (last topic id, last GitHub page).
- **Idempotency**: upserts by `(source_id, external_id)`.
- **Reproducibility**: pin Python deps; store raw responses in `data/cache/` for debugging.
- **Privacy/License**: store source URL + license; attribute in any UI surface.
- **Scheduling**: run `crawl` daily, `normalize` after crawl, `export` for LLM on demand.

---

## 14) Example Records

```json
{
  "title": "Hallway Nightlight (Motion + Illuminance)",
  "use_case": "nightlight",
  "triggers": ["motion_detected"],
  "conditions": ["illuminance_below", "time_range"],
  "actions": ["turn_on_light", "delay", "turn_off_light"],
  "entities": [{"domain":"binary_sensor","device_class":"motion"},{"domain":"sensor","device_class":"illuminance"},{"domain":"light"}],
  "integrations": ["zha","hue","zigbee2mqtt"],
  "brands": ["Aqara","Philips Hue"],
  "complexity": "low",
  "tags": ["lighting","presence","sleep"],
  "score": 0.73
}
```

---

## 15) Minimal Implementation Hints

**HTTP utils**: shared `httpx.Client` with retries, etag/if-none-match caching.  
**YAML tools**: safely load with `yaml.safe_load`; never execute jinja/templates.  
**Text**: strip HTML → markdown → plain text; split into sentences for NER/regex.  
**NLP**: start regex-first; add embeddings later if needed.  
**Security**: validate URLs; whitelist domains; block arbitrary file schemes.  

---

## 16) Roadmap

- v0: Discourse + GitHub, SQLite, CLI suggest/export, basic prompts
- v1: Add Cookbook/Node-RED, SimHash dedupe, embeddings for semantic similarity
- v2: Web dashboard for browsing corpus, “works-with” graphs, user feedback loop
