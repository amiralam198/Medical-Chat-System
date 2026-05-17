import re
from typing import Dict


PUBMED_JOURNAL_QUERY = (
    '"BMJ"[jour] OR "Br Med J"[jour] OR "Lancet"[jour] OR "Nature"[jour] OR '
    '"JAMA"[jour] OR "JAMA Intern Med"[jour] OR "N Engl J Med"[jour] OR '
    '"Ann Intern Med"[jour] OR "Diabetes Care"[jour] OR "Diabetologia"[jour] OR '
    '"Circulation"[jour] OR "J Am Heart Assoc"[jour] OR "Eur Heart J"[jour] OR '
    '"Circ Res"[jour] OR "Stroke"[jour]'
)

ISO_ALLOWLIST = {
    "bmj": "BMJ",
    "brmedj": "Br Med J",
    "lancet": "Lancet",
    "nature": "Nature",
    "jamainternmed": "JAMA Intern Med",
    "jama": "JAMA",
    "nengljmed": "N Engl J Med",
    "anninternmed": "Ann Intern Med",
    "diabetescare": "Diabetes Care",
    "diabetologia": "Diabetologia",
    "circulation": "Circulation",
    "jamheartassoc": "J Am Heart Assoc",
    "eurheartj": "Eur Heart J",
    "circres": "Circ Res",
    "stroke": "Stroke",
}

JOURNAL_TIER_SCORES: Dict[str, float] = {
    "lancet": 1.00,
    "nature": 1.00,
    "nengljmed": 0.98,
    "jamainternmed": 0.93,
    "jama": 0.96,
    "anninternmed": 0.92,
    "eurheartj": 0.95,
    "circulation": 0.93,
    "diabetescare": 0.90,
    "circres": 0.90,
    "stroke": 0.90,
    "diabetologia": 0.88,
    "bmj": 0.86,
    "brmedj": 0.86,
    "jamheartassoc": 0.82,
}


def normalize_journal(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


def trusted_journal_name(iso_abbreviation: str) -> str:
    normalized = normalize_journal(iso_abbreviation)
    for allowed_norm, display_name in ISO_ALLOWLIST.items():
        if allowed_norm in normalized or normalized in allowed_norm:
            return display_name
    return ""


def is_trusted_journal(iso_abbreviation: str) -> bool:
    return bool(trusted_journal_name(iso_abbreviation))


def journal_tier_score(iso_abbreviation: str) -> float:
    normalized = normalize_journal(iso_abbreviation)
    for allowed_norm, score in JOURNAL_TIER_SCORES.items():
        if allowed_norm in normalized or normalized in allowed_norm:
            return score
    return 0.0
