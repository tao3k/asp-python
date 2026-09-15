"""Service algorithms."""


def nested(enabled: bool, ready: bool, valid: bool, active: bool) -> int:
    if enabled:
        if ready:
            if valid:
                if active:
                    return 1
    return 0


def route(kind: str) -> int:
    if kind == "alpha":
        return 1
    elif kind == "beta":
        return 2
    elif kind == "gamma":
        return 3
    elif kind == "delta":
        return 4
    return 0


def traverse(groups: list[list[int]]) -> int:
    total = 0
    for group in groups:
        for value in group:
            if value > 10:
                total += value
            elif value < 0:
                total -= value
            elif value == 0:
                total += 0
            else:
                total += 1
    return total


def summarize(value: int) -> int:
    step_0 = value + 0
    step_1 = value + 1
    step_2 = value + 2
    step_3 = value + 3
    step_4 = value + 4
    step_5 = value + 5
    step_6 = value + 6
    step_7 = value + 7
    step_8 = value + 8
    step_9 = value + 9
    step_10 = value + 10
    step_11 = value + 11
    step_12 = value + 12
    step_13 = value + 13
    step_14 = value + 14
    return (
        step_0
        + step_1
        + step_2
        + step_3
        + step_4
        + step_5
        + step_6
        + step_7
        + step_8
        + step_9
        + step_10
        + step_11
        + step_12
        + step_13
        + step_14
    )


def has_admin(values: list[str]) -> bool:
    total = 0
    for value in values:
        total += len(value)
    counts = {}
    groups = {}
    for value in values:
        if value not in counts:
            counts[value] = 0
        counts[value] += 1
    for value in values:
        if value not in groups:
            groups[value] = []
        groups[value].append(value)
    names = []
    for value in values:
        if value:
            names.append(value.strip())
    for name in names:
        if name == "admin":
            return True
    return False
