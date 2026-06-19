"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    if max_price is not None:
        price_filtered = []
        for listing in listings:
            if listing["price"] <= max_price:
                price_filtered.append(listing)
        listings = price_filtered

    if size is not None:
        size_lower = size.lower()
        size_filtered = []
        for listing in listings:
            if size_lower in listing["size"].lower():
                size_filtered.append(listing)
        listings = size_filtered

    keywords = description.lower().split()

    scored = []
    for listing in listings:
        searchable = " ".join([
            listing["title"],
            listing["description"],
            " ".join(listing["style_tags"]),
        ]).lower()

        score = 0
        for keyword in keywords:
            if keyword in searchable:
                score += 1

        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda entry: entry[0], reverse=True)
    return [listing for score, listing in scored[:5]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    item_details = (
        f"Item: {new_item.get('title', 'Unknown')}\n"
        f"Category: {new_item.get('category', 'Unknown')}\n"
        f"Style tags: {', '.join(new_item.get('style_tags', []))}\n"
        f"Colors: {', '.join(new_item.get('colors', []))}\n"
        f"Description: {new_item.get('description', '')}"
    )

    wardrobe_items = wardrobe.get("items", [])

    if not wardrobe_items:
        prompt = (
            f"I'm considering buying this secondhand item:\n{item_details}\n\n"
            "I don't have a wardrobe on file yet. Give me general styling advice: "
            "what kinds of pieces pair well with this item, what vibe it suits, "
            "and how to build an outfit around it. Keep it to 2-3 sentences."
        )
    else:
        wardrobe_text = ""
        for item in wardrobe_items:
            wardrobe_text += (
                f"- {item['name']} ({item['category']}), "
                f"colors: {', '.join(item['colors'])}, "
                f"style: {', '.join(item['style_tags'])}\n"
            )

        prompt = (
            f"I'm considering buying this secondhand item:\n{item_details}\n\n"
            f"Here are the pieces already in my wardrobe:\n{wardrobe_text}\n"
            "Suggest 1-2 complete outfits using the new item paired with specific "
            "pieces from my wardrobe. Name each wardrobe piece and explain why it works. "
            "Keep it to 2-3 short paragraphs."
        )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception:
        return "Outfit suggestion unavailable."


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "Could not generate a fit card: no outfit suggestion was provided."

    client = _get_groq_client()

    title = new_item.get("title", "this piece")
    price = new_item.get("price", "unknown")
    platform = new_item.get("platform", "a resale platform")
    style_tags = ", ".join(new_item.get("style_tags", []))

    prompt = (
        f"Write a 2-4 sentence Instagram/TikTok caption for this thrifted outfit.\n\n"
        f"Item: {title} — ${price} from {platform}\n"
        f"Style: {style_tags}\n"
        f"Outfit: {outfit}\n\n"
        "The caption should feel casual and authentic, like a real OOTD post — "
        "not a product description. Mention the item name, price, and platform "
        "naturally (each once). Capture the outfit vibe in specific terms. "
        "No hashtags."
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=1.4,
        )
        return response.choices[0].message.content
    except Exception:
        return "Could not generate a fit card right now."
