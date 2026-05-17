import asyncio
import datetime as dt
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

import httpx

from agents.schemas import PubMedRecord
from retrieval.trusted_journals import PUBMED_JOURNAL_QUERY, is_trusted_journal


LOGGER = logging.getLogger(__name__)
ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def build_pubmed_query(user_query: str, recency_years: Optional[int] = None) -> str:
    scoped_query = "(%s) AND (%s)" % (user_query, PUBMED_JOURNAL_QUERY)
    if recency_years:
        current_year = dt.datetime.now().year
        start_year = max(1800, current_year - int(recency_years) + 1)
        scoped_query = "%s AND (%s:%s[pdat])" % (scoped_query, start_year, current_year)
    return scoped_query


async def fetch_pubmed_records(
    user_query: str,
    email: str,
    timeout_s: float,
    retmax: int,
    recency_years: Optional[int] = None,
) -> Tuple[List[PubMedRecord], str, str]:
    pubmed_query = build_pubmed_query(user_query, recency_years=recency_years)
    params = {
        "db": "pubmed",
        "term": pubmed_query,
        "retmode": "json",
        "retmax": str(retmax),
        "sort": "relevance",
        "email": email,
    }

    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            search_response = await client.get(ESEARCH_URL, params=params)
            search_response.raise_for_status()
            search_payload = search_response.json()
            pmids = search_payload.get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return [], pubmed_query, "No PubMed records matched the allowlisted journal query."

            await asyncio.sleep(0.35)
            records = await _efetch_records(client, pmids, email=email)
    except Exception as exc:
        LOGGER.exception("PubMed retrieval failed")
        error_text = str(exc) or exc.__class__.__name__
        return [], pubmed_query, "PubMed retrieval failed: %s" % error_text

    trusted_records = [record for record in records if is_trusted_journal(record.journal)]
    if records and not trusted_records:
        return (
            [],
            pubmed_query,
            "PubMed returned records, but none passed journal allowlist post-verification.",
        )

    return trusted_records, pubmed_query, ""


async def _efetch_records(
    client: httpx.AsyncClient,
    pmids: List[str],
    email: str,
) -> List[PubMedRecord]:
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "email": email,
    }
    response = await client.get(EFETCH_URL, params=params)
    response.raise_for_status()
    return parse_pubmed_xml(response.text)


def parse_pubmed_xml(xml_text: str) -> List[PubMedRecord]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        LOGGER.exception("Unable to parse PubMed XML")
        return []

    records = []
    for pubmed_article in root.findall(".//PubmedArticle"):
        record = _parse_pubmed_article(pubmed_article)
        if record:
            records.append(record)
    return records


def _parse_pubmed_article(pubmed_article: ET.Element) -> Optional[PubMedRecord]:
    medline = pubmed_article.find("MedlineCitation")
    if medline is None:
        return None

    article = medline.find("Article")
    if article is None:
        return None

    pmid = _node_text(medline.find("PMID"))
    if not pmid:
        return None

    title = _node_text(article.find("ArticleTitle")) or "Untitled PubMed record"
    journal_node = article.find("Journal")
    journal_iso = ""
    if journal_node is not None:
        journal_iso = _node_text(journal_node.find("ISOAbbreviation")) or _node_text(
            journal_node.find("Title")
        )

    abstract = _parse_abstract(article)
    publication_types = [
        _node_text(node)
        for node in article.findall("./PublicationTypeList/PublicationType")
        if _node_text(node)
    ]
    doi = _parse_doi(pubmed_article)
    year = _parse_year(article)

    return PubMedRecord(
        pmid=pmid,
        title=title,
        journal=journal_iso,
        year=year,
        abstract=abstract,
        publication_types=publication_types,
        doi=doi,
        url="https://pubmed.ncbi.nlm.nih.gov/%s/" % pmid,
    )


def _node_text(node: Optional[ET.Element]) -> str:
    if node is None:
        return ""
    return " ".join("".join(node.itertext()).split())


def _parse_abstract(article: ET.Element) -> str:
    abstract_nodes = article.findall("./Abstract/AbstractText")
    blocks = []
    for node in abstract_nodes:
        text = _node_text(node)
        if not text:
            continue
        label = node.attrib.get("Label") or node.attrib.get("NlmCategory")
        if label:
            blocks.append("%s: %s" % (label.strip(), text))
        else:
            blocks.append(text)
    return " ".join(blocks)


def _parse_doi(pubmed_article: ET.Element) -> Optional[str]:
    for node in pubmed_article.findall(".//ArticleId"):
        if node.attrib.get("IdType", "").lower() == "doi":
            doi = _node_text(node)
            if doi:
                return doi
    for node in pubmed_article.findall(".//ELocationID"):
        if node.attrib.get("EIdType", "").lower() == "doi":
            doi = _node_text(node)
            if doi:
                return doi
    return None


def _parse_year(article: ET.Element) -> Optional[int]:
    year_candidates = [
        article.findtext("./ArticleDate/Year"),
        article.findtext("./Journal/JournalIssue/PubDate/Year"),
    ]
    medline_date = article.findtext("./Journal/JournalIssue/PubDate/MedlineDate")
    if medline_date:
        match = re.search(r"(18|19|20)\d{2}", medline_date)
        if match:
            year_candidates.append(match.group(0))
    for value in year_candidates:
        if value and value.isdigit():
            return int(value)
    return None
