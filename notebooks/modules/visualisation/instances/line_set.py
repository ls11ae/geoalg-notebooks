from typing import Optional

from ...geometry import Point, Line
from ..drawing import DrawingMode
from ..drawing_modes import LineMode
from itertools import chain
import numpy as np

from ..instance_handle import InstanceHandle


class LineSetInstance(InstanceHandle[set[Line]]):
    #make bot_left and top_right equal to the canvases bottom right and topright corner to makes sure lines are drawn correctly
    def __init__(self, bot_left : Point, top_right : Point, drawing_mode: Optional[DrawingMode] = None):
        self._bot_left = bot_left
        self._top_right = top_right
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
        points: list[Point] = []
        for point in super().generate_random_points(max_x, max_y, number // 2):
            points.append(point)
            scale = np.random.uniform(0.01, 0.05)
            x = np.clip(np.random.normal(point.x, scale * max_x), 0.05 * max_x, 0.95 * max_x)
            y = np.clip(np.random.normal(point.y, scale * max_y), 0.05 * max_y, 0.95 * max_y)
            points.append(Point(x, y))

        if number % 2 == 1:
            points.extend(super().generate_random_points(max_x, max_y, 1))
        return points