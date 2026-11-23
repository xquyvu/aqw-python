import json
from bisect import bisect_right

RANK_THRESHOLDS = (0, 900, 3600, 10000, 22500, 44100, 78400, 129600, 202500, 302500)


def rank_from_points(points: int) -> int:
    return max(1, bisect_right(RANK_THRESHOLDS, points))


def checkOperator(obj1, obj2, operator: str):
    if operator == ">=":
        return obj1 >= obj2
    if operator == ">":
        return obj1 > obj2
    if operator == "<=":
        return obj1 <= obj2
    if operator == "<":
        return obj1 < obj2
    if operator == "==":
        return obj1 == obj2
    if operator == "!=":
        return obj1 != obj2
    raise ValueError(f"unsupported operator: {operator!r}")


def normalize(text: str):
    return text.lower().strip().replace("`", "'").replace("❜", "'").replace("’", "'")


def is_valid_json(s):
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False
