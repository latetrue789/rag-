import re

from app.services.retrieval import Source

CITATION_PATTERN = re.compile(r"\[(S\d+)]")


def cited_source_ids(answer: str) -> set[str]:
    return set(CITATION_PATTERN.findall(answer))


def has_valid_citations(answer: str, sources: list[Source]) -> bool:
    cited = cited_source_ids(answer)
    allowed = {source.source_id for source in sources}
    return bool(cited) and cited <= allowed
