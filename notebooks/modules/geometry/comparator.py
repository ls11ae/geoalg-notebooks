from __future__ import annotations
from .core import Comparator, ComparisonResult, Point

from typing_extensions import override

class IntComparator(Comparator[int]):
    def compare(self, key: int, other: int) -> ComparisonResult :
        if key > other:
            return ComparisonResult.AFTER
        elif key < other:
            return ComparisonResult.BEFORE
        else:
            return ComparisonResult.MATCH

class FloatComparator(Comparator[float]):
    @override
    def compare(self, key: float, other: float) -> ComparisonResult:
        if key > other:
            return ComparisonResult.AFTER
        elif key < other:
            return ComparisonResult.BEFORE
        else:
            return ComparisonResult.MATCH

class PointXComparator(Comparator[Point]):
    def __init__(self):
        self._number_comparator = FloatComparator()

    @override
    def compare(self, key: Point, other: Point) -> ComparisonResult:
        return self._number_comparator.compare(key.x, other.x)


class PointYComparator(Comparator[Point]):
    def __init__(self):
        self._number_comparator = FloatComparator()

    @override
    def compare(self, key: Point, other: Point) -> ComparisonResult:
        return self._number_comparator.compare(key.y, other.y)