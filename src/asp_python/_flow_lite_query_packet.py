"""Render semantic-flow-lite compact and JSON packet output."""

from __future__ import annotations

from pathlib import Path

from ._flow_lite_query_model import (
    _FLOW_LITE_CATALOG_ID,
    _FLOW_LITE_FLOW_KIND,
    _FlowLiteOccurrence,
    _FlowLiteResult,
)
from ._flow_lite_query_projector import _evaluate_flow_lite_query


def _parse_flow_lite_where(value: str) -> dict[str, str]:
    where: dict[str, str] = {}
    for constraint in value.split():
        key, _separator, raw_value = constraint.partition("=")
        where[key] = raw_value
    return {
        "source.call": where["source.call"],
        "sink.constructs": where["sink.constructs"],
        "scope.fn": where["scope.fn"],
    }


def _flow_lite_frontier(project_root: Path, where: dict[str, str]) -> str:
    result = _evaluate_flow_lite_query(project_root, where)
    source = _occurrence(result, "source")
    sink = _occurrence(result, "sink")
    confidence = _flow_lite_confidence(result)
    scope_fn = where["scope.fn"]
    return "\n".join(
        [
            f"[query-flow-lite] root={project_root} lang=python catalog=flow-lite "
            f"flow={_FLOW_LITE_FLOW_KIND} scope=fn({scope_fn}) alg=native-flow-lite",
            "legend: ID=kind:role(value)!next; edge SRC>{DST:rel}; frontier ID.next",
            "aliases=G:query,F:flow,S:source,K:sink,P:path",
            "",
            f"F=flow:local-source-sink(fn:{scope_fn})!flow",
            *([] if source is None else [_flow_lite_line("S", "source", source)]),
            *([] if sink is None else [_flow_lite_line("K", "sink", sink)]),
            _flow_lite_path_line(scope_fn, source, sink),
            "",
            "G>{F:selects}",
            _flow_lite_edges(source, sink),
            "",
            _flow_lite_confidence_line(result, confidence),
            f"rank={_flow_lite_rank(source, sink)}",
            f"frontier={_flow_lite_frontier_ids(source, sink)}",
            "omit=code,full-path-ast,raw-source",
            "avoid=raw-read,inline-code",
            *_flow_lite_note_lines(where, result, confidence),
        ]
    )


def _flow_lite_packet(project_root: Path, where: dict[str, str]) -> dict[str, object]:
    result = _evaluate_flow_lite_query(project_root, where)
    source = _occurrence(result, "source")
    sink = _occurrence(result, "sink")
    return {
        "schemaId": "agent.semantic-protocols.semantic-flow-lite",
        "schemaVersion": "1",
        "protocolId": "agent.semantic-protocols.semantic-language",
        "protocolVersion": "1",
        "languageId": "python",
        "providerId": "asp-python",
        "projectRoot": str(project_root),
        "packageName": project_root.name,
        "flowId": (
            f"flow-lite:{result['owner_path']}:"
            f"{where['scope.fn']}:{where['source.call']}:{where['sink.constructs']}"
        ),
        "flowKind": _FLOW_LITE_FLOW_KIND,
        "scope": "function",
        "ownerPath": result["owner_path"],
        "sourceAuthority": "native-parser",
        "executionBackend": "native-parser",
        "adapterMode": "native-projection",
        "sourceHandle": _flow_lite_handle(source, "call", where["source.call"]),
        "sinkHandle": _flow_lite_handle(sink, "constructs", where["sink.constructs"]),
        "path": _flow_lite_path_steps(source, sink, where["scope.fn"]),
        "guards": [],
        "effects": [],
        "artifacts": [],
        "confidence": _flow_lite_confidence(result),
        "omissions": _flow_lite_omissions(where, result),
        "fields": {
            "catalog": _FLOW_LITE_CATALOG_ID,
            "where": where,
            "scannedFiles": result["scanned_files"],
            "rawSourceStored": False,
        },
    }


def _occurrence(result: _FlowLiteResult, key: str) -> _FlowLiteOccurrence | None:
    value = result[key]
    return value if isinstance(value, dict) else None


def _flow_lite_confidence_line(result: _FlowLiteResult, confidence: str) -> str:
    return (
        f"confidence={confidence} sourceAuthority=native-parser "
        "executionBackend=native-parser adapterMode=native-projection "
        f"owner={result['owner_path']} "
        f"range={result['function_start']}:{result['function_end']} "
        f"scannedFiles={result['scanned_files']}"
    )


def _flow_lite_line(prefix: str, role: str, occurrence: _FlowLiteOccurrence) -> str:
    return (
        f"{prefix}={role}:{occurrence['kind']}({occurrence['value']})"
        f"@{occurrence['path']}:{occurrence['line']}!code"
    )


def _flow_lite_path_line(
    scope_fn: str,
    source: _FlowLiteOccurrence | None,
    sink: _FlowLiteOccurrence | None,
) -> str:
    if source is not None and sink is not None:
        return "P=path:bounded(S->K)!flow"
    return f"P=path:unavailable(fn:{scope_fn})!flow"


def _flow_lite_edges(
    source: _FlowLiteOccurrence | None,
    sink: _FlowLiteOccurrence | None,
) -> str:
    if source is not None and sink is not None:
        return "F>{S:source,K:sink,P:flows-to}\nS>{K:flows-to}"
    if source is not None:
        return "F>{S:source,P:unavailable}"
    if sink is not None:
        return "F>{K:sink,P:unavailable}"
    return "F>{P:unavailable}"


def _flow_lite_rank(
    source: _FlowLiteOccurrence | None,
    sink: _FlowLiteOccurrence | None,
) -> str:
    ids = ["P"]
    if source is not None:
        ids.insert(0, "S")
    if sink is not None:
        ids.insert(-1, "K")
    return ",".join(ids)


def _flow_lite_frontier_ids(
    source: _FlowLiteOccurrence | None,
    sink: _FlowLiteOccurrence | None,
) -> str:
    ids = ["P.flow"]
    if source is not None:
        ids.insert(0, "S.code")
    if sink is not None:
        ids.insert(-1, "K.code")
    return ",".join(ids)


def _flow_lite_note_lines(
    where: dict[str, str],
    result: _FlowLiteResult,
    confidence: str,
) -> list[str]:
    if confidence == "bounded":
        return []
    notes = ";".join(
        str(omission["message"]) for omission in _flow_lite_omissions(where, result)
    )
    return [f"note={notes}"]


def _flow_lite_confidence(result: _FlowLiteResult) -> str:
    if result["source"] is not None and result["sink"] is not None:
        return "bounded"
    if result["owner_path"] != "." and (
        result["source"] is not None or result["sink"] is not None
    ):
        return "partial"
    return "unavailable"


def _flow_lite_omissions(
    where: dict[str, str],
    result: _FlowLiteResult,
) -> list[dict[str, object]]:
    if result["owner_path"] == ".":
        return [
            _flow_lite_omission(
                "scope.fn", f"scope.fn `{where['scope.fn']}` was not found"
            )
        ]
    omissions: list[dict[str, object]] = []
    if result["source"] is None:
        omissions.append(
            _flow_lite_omission(
                "source.call",
                f"source.call `{where['source.call']}` was not found in scope.fn `{where['scope.fn']}`",
            )
        )
    if result["sink"] is None:
        omissions.append(
            _flow_lite_omission(
                "sink.constructs",
                f"sink.constructs `{where['sink.constructs']}` was not found in scope.fn `{where['scope.fn']}`",
            )
        )
    return omissions


def _flow_lite_omission(target: str, message: str) -> dict[str, object]:
    return {"kind": "unavailable", "message": message, "target": target}


def _flow_lite_handle(
    occurrence: _FlowLiteOccurrence | None,
    kind: str,
    fallback: str,
) -> str:
    return f"{kind}:{fallback}" if occurrence is None else str(occurrence["handle"])


def _flow_lite_path_steps(
    source: _FlowLiteOccurrence | None,
    sink: _FlowLiteOccurrence | None,
    scope_fn: str,
) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    if source is not None:
        steps.append(_flow_lite_path_step("step.1", source, "source"))
    if sink is not None:
        steps.append(_flow_lite_path_step("step.2", sink, "sink"))
    if source is not None and sink is not None:
        steps.append(_flow_lite_flow_step(source, sink, scope_fn))
    return steps


def _flow_lite_path_step(
    step_id: str,
    occurrence: _FlowLiteOccurrence,
    relation: str,
) -> dict[str, object]:
    return {
        "id": step_id,
        "handle": occurrence["handle"],
        "relation": relation,
        "location": {
            "path": occurrence["path"],
            "lineRange": _line_range(int(occurrence["line"])),
        },
        "evidenceRefs": ["native-flow-lite.1"],
        "fields": {
            "value": occurrence["value"],
            "kind": occurrence["kind"],
        },
    }


def _flow_lite_flow_step(
    source: _FlowLiteOccurrence,
    sink: _FlowLiteOccurrence,
    scope_fn: str,
) -> dict[str, object]:
    return {
        "id": "step.3",
        "handle": sink["handle"],
        "relation": "flows-to",
        "location": {
            "path": sink["path"],
            "lineRange": _line_range(int(sink["line"])),
        },
        "evidenceRefs": ["native-flow-lite.1"],
        "fields": {"from": source["handle"], "to": sink["handle"], "scopeFn": scope_fn},
    }


def _line_range(line: int) -> dict[str, int]:
    return {"start": line, "end": line}
