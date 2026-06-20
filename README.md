# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---

### `search_listings(description, size, max_price)`

**Purpose:** Filters the 40 mock listings to those whose title, description, or style tags match the user's keyword phrase, whose size contains the user's size (case-insensitive), and whose price is at or below the limit. Returns the top 5 matches ranked by how many keywords appear in the listing.

| Parameter | Type | Meaning |
|---|---|---|
| `description` | `str` | Natural-language keyword phrase (e.g. `"vintage graphic tee"`). Matched against each listing's title, description, and style_tags. |
| `size` | `str \| None` | Clothing size to filter by (e.g. `"M"`, `"S/M"`). Pass `None` to skip size filtering. Matching is case-insensitive substring — `"M"` matches `"S/M"`. |
| `max_price` | `float \| None` | Upper price limit in dollars (inclusive). Pass `None` to skip price filtering. |

**Returns:** `list[dict]` — up to 5 listing dicts sorted by relevance, highest first. Each dict has: `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list[str]), `size` (str), `condition` (str), `price` (float), `colors` (list[str]), `brand` (str or None), `platform` (str). Returns `[]` if nothing matches — does not raise an exception.

---

### `suggest_outfit(new_item, wardrobe)`

**Purpose:** Sends the new listing item and the user's wardrobe to the Groq LLM (`llama-3.3-70b-versatile`) and asks it to suggest 1–2 complete outfit combinations, naming specific wardrobe pieces and explaining the styling reasoning.

| Parameter | Type | Meaning |
|---|---|---|
| `new_item` | `dict` | A listing dict from `search_listings` — uses `title`, `category`, `style_tags`, `colors`, and `description`. |
| `wardrobe` | `dict` | Wardrobe dict with an `"items"` key containing a list of wardrobe item dicts (each with `name`, `category`, `colors`, `style_tags`). May be empty. |

**Returns:** `str` — one to three short paragraphs naming wardrobe pieces and explaining pairings. If the wardrobe is empty, the LLM is still called but asked for general styling advice instead of specific pairings. Returns `"Outfit suggestion unavailable."` if the API call raises an exception.

---

### `create_fit_card(outfit, new_item)`

**Purpose:** Sends the outfit suggestion and listing details to the Groq LLM and asks it to write a 2–4 sentence Instagram/TikTok-style caption — casual and authentic, mentioning the item name, price, and platform once each. Uses `temperature=1.4` so the output varies across runs.

| Parameter | Type | Meaning |
|---|---|---|
| `outfit` | `str` | The outfit suggestion string from `suggest_outfit`. If empty or whitespace-only, the function returns an error string without calling the LLM. |
| `new_item` | `dict` | The listing dict for the item — uses `title`, `price`, `platform`, and `style_tags` to build the prompt. |

**Returns:** `str` — a short social-media-style caption. Returns `"Could not generate a fit card: no outfit suggestion was provided."` if `outfit` is empty. Returns `"Could not generate a fit card right now."` if the API call raises an exception.

---

## Interaction Walkthrough

**User query:** "looking for a vintage graphic tee under $30"

**Step 1 — Tool called: `search_listings`**
- **Input:** `description="vintage graphic tee"`, `size=None`, `max_price=30.0`
- **Why this tool:** The planning loop always starts here. Before suggesting an outfit or generating a caption, the agent needs to find an actual listing to work with. The LLM first parsed the query to extract these three values (`_parse_query`); size was not mentioned so it was set to `None`.
- **Output:** A list containing `lst_002` — `"Y2K Baby Tee — Butterfly Print"`, size `S/M`, `$18.00`, platform `depop`. The planning loop sets `session["selected_item"] = results[0]`.

**Step 2 — Tool called: `suggest_outfit`**
- **Input:** `new_item=session["selected_item"]` (the Y2K Baby Tee dict), `wardrobe=session["wardrobe"]` (the 10-item example wardrobe)
- **Why this tool:** The agent now has a concrete item. The next step is to suggest how it fits into the user's existing wardrobe before producing the final card.
- **Output:** A paragraph suggesting the baggy straight-leg jeans and chunky white sneakers as the primary pairing (shared streetwear/y2k style tags), with the vintage black denim jacket as an optional layer. Stored in `session["outfit_suggestion"]`.

**Step 3 — Tool called: `create_fit_card`**
- **Input:** `outfit=session["outfit_suggestion"]`, `new_item=session["selected_item"]`
- **Why this tool:** The agent has both the item and the styling context. This tool generates the final user-facing output — a shareable caption that wraps everything together.
- **Output:** A 2–4 sentence caption mentioning the Y2K Baby Tee, the $18 price, depop, and the outfit vibe. Stored in `session["fit_card"]` and returned to the user.

**Final output to user (from actual test run):**
```
Found: Y2K Baby Tee — Butterfly Print

Outfit: To style the Y2K Baby Tee, consider pairing it with the Baggy
Straight-Leg Jeans for a casual, streetwear-inspired look. The contrast
between the fitted, crop-length tee and the loose-fitting jeans creates a
balanced silhouette...

Fit card: I'm obsessed with my new Y2K Baby Tee that I scored on Depop for
$18.0 - it's giving me all the playful, vintage vibes. I styled it with some
Baggy Straight-Leg Jeans and Chunky White Sneakers for a casual,
streetwear-inspired look that's perfect for a laid-back day out.
```

---

## Planning Loop

The tool call order is always fixed: `search_listings` → `suggest_outfit` → `create_fit_card`. There is no dynamic branching between tools. The planning loop (`run_agent` in `agent.py`) first calls `_parse_query`, which sends the user's natural-language query to the Groq LLM at `temperature=0` and asks it to return a JSON object with `description`, `size`, and `max_price`. These three values are written into `session["parsed"]` and then passed directly to `search_listings`.

After `search_listings`, the loop checks the result: if the list is empty it sets `session["error"]` to a message that quotes back the searched values and returns early — `suggest_outfit` and `create_fit_card` are never called. If the list is non-empty, `results[0]` is stored as `session["selected_item"]` and the loop continues. The remaining two tool calls always execute and always produce a non-empty string, so there is no second early-exit point.

---

## State Management

All state lives in a single session dict (`_new_session` in `agent.py`). No tool reads from the previous tool's output directly — the planning loop pulls values out of the session and passes them as arguments. `wardrobe` is loaded once before the query runs and never modified. `description`, `size`, `max_price`, `selected_item`, `outfit_suggestion`, and `fit_card` are all written during the run. The key handoffs are: `search_results[0]` → `session["selected_item"]` → passed as `new_item` to both `suggest_outfit` and `create_fit_card`; and `session["outfit_suggestion"]` → passed as `outfit` to `create_fit_card`.

---

## Error Handling and Fail Points

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | Returns `[]` — no listings matched the description, size, and price filters | Sets `session["error"]` to `"No listings matched '[description]' in size [size] under $[max_price]. Try a broader keyword, a different size, or a higher price limit."` — quoting back the exact values searched. Returns the session immediately; `suggest_outfit` and `create_fit_card` are not called. **Confirmed in testing:** query `"designer ballgown size XXS under $5"` produced `"No listings matched 'designer ballgown' in size XXS under $5.0. Try a broader keyword, a different size, or a higher price limit."` |
| `suggest_outfit` | Groq API raises an exception (timeout, bad key, rate limit) | Catches the exception and returns `"Outfit suggestion unavailable."` — the planning loop stores this string in `session["outfit_suggestion"]` and continues to `create_fit_card` rather than stopping. The user receives a fit card with the fallback string in the outfit panel. |
| `suggest_outfit` | `wardrobe["items"]` is `[]` (new user with no wardrobe) | Still calls the LLM but with a different prompt asking for general styling advice (what kinds of pieces pair well, what vibe it suits). Returns a non-empty string so `create_fit_card` always receives valid input. |
| `create_fit_card` | `outfit` is an empty or whitespace-only string | Returns `"Could not generate a fit card: no outfit suggestion was provided."` without calling the LLM. Does not raise an exception. |

---

## Spec Reflection

**One way planning.md helped during implementation:**

Writing out the State Management table — specifically the "Set when" and "Used by" columns — made it immediately obvious that `wardrobe` should be loaded once before the loop and never re-loaded inside it. When implementing `run_agent`, I could see at a glance that `session["wardrobe"]` was the source for `suggest_outfit`, not a fresh `get_example_wardrobe()` call inside the function. Without that table I likely would have re-loaded the wardrobe inside the loop, which would have broken the "empty wardrobe" test case since the test passes in `get_empty_wardrobe()` but a re-load would override it with the example.

**One divergence from your spec, and why:**

The planning.md spec for `create_fit_card` described it as a pure string formatter — a fixed template with labeled fields like `Price: $18.0`, `Platform: depop`, and so on. The actual stub in `tools.py`, however, specified that `create_fit_card` should call the LLM to generate a casual Instagram/TikTok-style caption rather than produce a structured card. I followed the stub because it is the graded interface, and because an LLM-generated caption produces a more natural and varied output than a template. The planning.md `create_fit_card` format ended up being used instead in `handle_query()` in `app.py` to populate the "Top listing found" panel.

---

## AI Usage

**Instance 1 — Implementing `search_listings`:**
I gave Claude the Tool 1 block from planning.md: the "what it does" description, all three input parameters with names/types/meanings, the full return value field list, and the empty-results failure mode. I asked it to implement `search_listings` in `tools.py` using `load_listings()` from the data loader. It produced a working function with the three filters and a keyword-scoring loop. Two things I changed before using it: (1) the size filter in the generated code used exact string equality (`l["size"] == size`), but the stub's docstring said matching should be case-insensitive with `"M"` matching `"S/M"`, so I changed it to `size_lower in listing["size"].lower()`; (2) the scoring used a nested generator expression (`sum(1 for kw in keywords if kw in searchable)`) that I rewrote as an explicit `score += 1` for loop because it was harder to read.

**Instance 2 — Implementing `run_agent`:**
I gave Claude the Planning Loop section, the State Management section, and the Mermaid architecture diagram from planning.md all at once. It produced a `run_agent` function that called all three tools in order. Before running it I checked three things against the spec: (1) the early-exit branch after `search_listings` was present — it was; (2) `selected_item` was set to `results[0]`, not the full list — it was; (3) `wardrobe` came from the session dict rather than being re-loaded inside the loop — it did. I did not need to override the logic, but I added `_parse_query` as a separate helper function to keep the LLM query-parsing step isolated from the main loop, which made both functions easier to read and test independently.

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
