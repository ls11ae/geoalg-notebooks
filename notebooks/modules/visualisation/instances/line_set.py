from typing import Optional, override
from itertools import chain

from ...geometry import Point, Line
from ..drawing import DrawingMode
from ..drawing_modes import LineMode
from ..instance_handle import InstanceHandle

class LineSetInstance(InstanceHandle[set[Line]]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = LineMode()
        super().__init__(set(), drawing_mode, 20)
        self._cached_point: Optional[Point] = None

    @override
    def add_point(self, point: Point) -> Point | None:
        if self._cached_point is None:
            self._cached_point = point
            return point
        elif self._cached_point == point:
            return None
        line = Line(self._cached_point, point)
        if line in self._instance:
            return None
        self._instance.add(line)
        self._cached_point = None
        return point

    @override
    def clear(self):
        self._instance.clear()
        self._cached_point = None

    @override
    def size(self) -> int:
        return len(self._instance)

    @staticmethod
    @override
    def extract_points_from_raw_instance(instance: set[Line]) -> list[Point]:
        return list(chain.from_iterable((line.p1, line.p2) for line in instance))

    @override
    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        if number % 2 != 0:
            number = number + 1
        return LineSetInstance.generate_random_points_uniform(max_x, max_y, number)