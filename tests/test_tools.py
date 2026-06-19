from unittest.mock import MagicMock, patch

from tools import create_fit_card, search_listings, suggest_outfit
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


# ── search_listings ───────────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []


def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)


# ── suggest_outfit ────────────────────────────────────────────────────────────

SAMPLE_ITEM = {
    "title": "Y2K Baby Tee — Butterfly Print",
    "category": "tops",
    "style_tags": ["y2k", "vintage", "graphic tee"],
    "colors": ["white", "pink"],
    "description": "Cute early 2000s baby tee with butterfly graphic.",
}


def test_suggest_outfit_with_wardrobe():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        "Pair with the baggy jeans and chunky sneakers."
    )

    with patch("tools._get_groq_client", return_value=mock_client):
        result = suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())

    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_empty_wardrobe():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        "Try styling this with high-waisted jeans and minimal accessories."
    )

    with patch("tools._get_groq_client", return_value=mock_client):
        result = suggest_outfit(SAMPLE_ITEM, get_empty_wardrobe())

    assert isinstance(result, str)
    assert len(result) > 0


def test_suggest_outfit_api_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API timeout")

    with patch("tools._get_groq_client", return_value=mock_client):
        result = suggest_outfit(SAMPLE_ITEM, get_example_wardrobe())

    assert result == "Outfit suggestion unavailable."


# ── create_fit_card ───────────────────────────────────────────────────────────

def test_create_fit_card_empty_outfit():
    result = create_fit_card("", SAMPLE_ITEM)
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_fit_card_whitespace_outfit():
    result = create_fit_card("   ", SAMPLE_ITEM)
    assert isinstance(result, str)
    assert len(result) > 0


def test_create_fit_card_api_error():
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API timeout")

    with patch("tools._get_groq_client", return_value=mock_client):
        result = create_fit_card("Pair with baggy jeans.", SAMPLE_ITEM)

    assert result == "Could not generate a fit card right now."


def test_create_fit_card_returns_caption():
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        "Found this Y2K baby tee on depop for $18 and I'm obsessed."
    )

    with patch("tools._get_groq_client", return_value=mock_client):
        result = create_fit_card("Pair with baggy jeans.", SAMPLE_ITEM)

    assert isinstance(result, str)
    assert len(result) > 0
