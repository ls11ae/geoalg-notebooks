from typing import Optional
from itertools import chain
import numpy as np

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

    def add_point(self, point: Point) -> bool:
        if self._cached_point is None:
            self._cached_point = point
            return True
        elif self._cached_point == point:
            return False
        line = Line(self._cached_point, point)
        if line in self._instance:
            return False
        self._instance.add(line)
        self._cached_point = None
        return True

    def clear(self):
        self._instance.clear()
        self._cached_point = None

    def size(self) -> int:
        return len(self._instance)

    @staticmethod
    def extract_points_from_raw_instance(instance: set[Line]) -> list[Point]:
        return list(chain.from_iterable((line.p1, line.p2) for line in instance))

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        if number % 2 != 0:
            number = number + 1
        return LineSetInstance.generate_random_points_uniform(max_x, max_y, number)