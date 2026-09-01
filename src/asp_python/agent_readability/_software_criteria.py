"""Shared software criterion labels for readability findings."""

from __future__ import annotations

SOFTWARE_CRITERION_LABEL = "softwareCriteria"

CONTROL_FLOW_BROAD_LINEAR_PHASE = "control-flow.broad-linear-phase"
CONTROL_FLOW_DECISION_STACK = "control-flow.decision-stack"
CONTROL_FLOW_LITERAL_DISPATCH_CHAIN = "control-flow.literal-dispatch-chain"
CONTROL_FLOW_TRAVERSAL_KNOT = "control-flow.traversal-knot"
NATIVE_IDIOM_MANUAL_TRANSFORM_LOOP = "native-idiom.manual-transform-loop"


def finding_labels(
    base_labels: dict[str, str],
    criterion_ids: tuple[str, ...],
) -> dict[str, str]:
    """Return finding labels with RFC 013 criterion ids attached."""

    labels = dict(base_labels)
    labels[SOFTWARE_CRITERION_LABEL] = ",".join(dict.fromkeys(criterion_ids))
    return labels
