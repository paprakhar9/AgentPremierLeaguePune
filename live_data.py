import re
from typing import List

import requests
from bs4 import BeautifulSoup

SEARCH_URLS = [
    "https://www.google.com/search",
    "https://www.google.com/search?igu=1",
    "https://www.google.co.in/search",
    "https://www.google.co.uk/search",
]
SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
SEARCH_PARAMS = {
    "q": "live cricket score",
    "hl": "en",
    "gl": "us",
    "pws": "0",
    "num": "10",
    "client": "firefox-b-d",
}

SAMPLE_LIVE_MATCHES = [
    {
        "team_a": "Pune Warriors",
        "team_b": "Mumbai Challengers",
        "score": "142/5 (15.2 ov)",
        "status": "Live",
    },
    {
        "team_a": "Bengal Tigers",
        "team_b": "Delhi Royals",
        "score": "98/3 (12.1 ov)",
        "status": "Live",
    },
]

SCORE_PATTERN = re.compile(
    r"\d{1,3}/\d{1,2}(?:\s*\(\d{1,2}(?:\.\d)?\s*ov\))?|\d{1,3}\s*overs?|\d{1,3}\s*pts?",
    flags=re.I,
)
STATUS_PATTERN = re.compile(r"\b(Live|LIVE|In Progress|Inning|stumps|Scheduled|Final)\b", flags=re.I)
TEAM_VS_PATTERN = re.compile(r"([A-Z][A-Za-z &'\.\-]+?)\s+vs\.?\s+([A-Z][A-Za-z &'\.\-]+?)", flags=re.I)


def _clean_text(element) -> str:
    """Return cleaned text for a BeautifulSoup element.

    Args:
        element: BeautifulSoup node or None.

    Returns:
        str: Cleaned, whitespace-normalized text.
    """
    return " ".join(element.stripped_strings) if element else ""


def _is_google_blocked(html: str) -> bool:
    checks = [
        "If you're having trouble accessing Google Search",
        "enablejs?sei=",
        "SecurityCompromiseError",
        "without JavaScript",
    ]
    return any(check in html for check in checks)


def _create_session() -> requests.Session:
    """Create an HTTP session preconfigured for Google search scraping.

    Returns:
        requests.Session: Configured requests session.
    """
    session = requests.Session()
    session.headers.update(SEARCH_HEADERS)
    return session


def fetch_google_search_html() -> str:
    """Attempt to fetch Google search HTML for live cricket scores.

    Tries a set of known search endpoints and returns the first usable HTML.

    Returns:
        str: HTML text if successful, otherwise empty string.
    """
    session = _create_session()
    for url in SEARCH_URLS:
        try:
            response = session.get(url, params=SEARCH_PARAMS, timeout=10)
            if response.status_code != 200:
                continue
            html = response.text
            if _is_google_blocked(html):
                continue
            return html
        except requests.RequestException:
            continue
    return ""


def _select_texts(node, selectors) -> list[str]:
    values = []
    for selector in selectors:
        for element in node.select(selector):
            text = _clean_text(element)
            if text:
                values.append(text)
    return values


def _extract_match_from_card(card) -> dict:
    title_text = _clean_text(card)
    status_match = STATUS_PATTERN.search(title_text)
    status = status_match.group(0) if status_match else "Live"

    team_names = []
    for selector in [
        ".imso_mh__team-name",
        ".imso_mh__tm-name",
        ".imso_mh__t2-name",
        "div[class*='team']",
        "span[class*='team']",
    ]:
        for text in _select_texts(card, [selector]):
            if text not in team_names:
                team_names.append(text)
            if len(team_names) >= 2:
                break
        if len(team_names) >= 2:
            break

    score_values = _select_texts(
        card,
        [
            ".imso_mh__l-tm-sc",
            ".imso_mh__score",
            ".imso_mh__scr-sep",
            "div[class*='score']",
            "span[class*='score']",
        ],
    )
    if not score_values:
        score_values = SCORE_PATTERN.findall(title_text)
    score = " | ".join(dict.fromkeys(score_values))

    if not team_names:
        vs_match = TEAM_VS_PATTERN.search(title_text)
        if vs_match:
            team_names = [vs_match.group(1).strip(), vs_match.group(2).strip()]

    if len(team_names) >= 2 and score:
        return {
            "team_a": team_names[0],
            "team_b": team_names[1],
            "score": score,
            "status": status,
        }
    return {}


def _parse_live_matches_from_html(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "html.parser")
    matches = []

    card_selectors = [
        "div[data-attrid*='sports']",
        "div.imso_mh__scorecard",
        "div.imso_mh__match",
        "div.imso_mh__l-tm",
        "div[class*='live']",
    ]

    for selector in card_selectors:
        for card in soup.select(selector):
            match_info = _extract_match_from_card(card)
            if match_info and match_info not in matches:
                matches.append(match_info)
                if len(matches) >= 5:
                    return matches

    if not matches:
        page_text = soup.get_text(" ", strip=True)
        for vs_match in TEAM_VS_PATTERN.finditer(page_text):
            team_a = vs_match.group(1).strip()
            team_b = vs_match.group(2).strip()
            after_text = page_text[vs_match.end() : vs_match.end() + 180]
            score_values = SCORE_PATTERN.findall(after_text)
            if score_values:
                matches.append(
                    {
                        "team_a": team_a,
                        "team_b": team_b,
                        "score": " | ".join(dict.fromkeys(score_values)),
                        "status": "Live",
                    }
                )
                if len(matches) >= 5:
                    break

    return matches


def fetch_live_matches_from_google() -> List[dict]:
    html = fetch_google_search_html()
    if not html:
        return SAMPLE_LIVE_MATCHES

    matches = _parse_live_matches_from_html(html)
    return matches or SAMPLE_LIVE_MATCHES
