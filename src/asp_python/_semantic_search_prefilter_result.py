"""Runtime metadata for Python semantic-search prefilters."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ._semantic_search_prefilter_rank import (
    MAX_PREFILTER_FILES_PER_TERM,
    MAX_PREFILTER_FILES_TOTAL,
)

MIN_PREFILTER_FILES = 128


@dataclass(frozen=True, slots=True)
class PythonSearchPrefilterResult:
    """Files selected before parser-owned fact extraction."""

    paths: tuple[Path, ...]
    total_files: int
    term_capped_files: int
    matched_files: int
    elapsed_ms: int
    tool: str
    reason: str
    query_terms: int
    source_search_passes: int
    file_list_passes: int
    candidate_file_basis: str

    def runtime_cost(self) -> dict[str, object]:
        """Return schema-owned runtime-cost metadata for the search packet."""

        return {
            "cacheStatus": "disabled",
            "elapsedMs": self.elapsed_ms,
            "sourceFilesParsed": self.matched_files,
            "reason": self.reason,
            "fields": {
                "prefilterTool": self.tool,
                "candidateFiles": self.total_files,
                "minCandidateFiles": MIN_PREFILTER_FILES,
                "termCappedFiles": self.term_capped_files,
                "matchedFiles": self.matched_files,
                "maxFilesPerTerm": MAX_PREFILTER_FILES_PER_TERM,
                "maxFilesTotal": MAX_PREFILTER_FILES_TOTAL,
                "mode": "text-query-prefilter",
                "queryTerms": self.query_terms,
                "sourceSearchPasses": self.source_search_passes,
                "fileListPasses": self.file_list_passes,
                "candidateFileBasis": self.candidate_file_basis,
            },
        }
