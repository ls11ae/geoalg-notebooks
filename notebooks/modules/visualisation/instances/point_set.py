from typing import Optional

from ...geometry import Point
from ..drawing import DrawingMode
from ..drawing_modes import PointsMode

import numpy as np

from ..instance_handle import InstanceHandle


class PointSetInstance(InstanceHandle[set[Point]]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = PointsMode()
        super().__init__(set(), drawing_mode, 250)

    def add_point(self, point: Point) -> bool:
        if point in self._instance:
            return False
        self._instance.add(point)

        return True

    def clear(self):
        self._instance.clear()

    def size(self) -> int:
        return len(self._instance)

    @staticmethod
    def extract_points_from_raw_instance(instance: set[Point]) -> list[Point]:
        return list(instance)

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        x_values = np.clip(np.random.normal(0.5 * max_x, 0.15 * max_x, number), 0.05 * max_x, 0.95 * max_x)
        y_values = np.clip(np.random.normal(0.5 * max_y, 0.15 * max_y, number), 0.05 * max_y, 0.95 * max_y)
        return [Point(x, y) for x, y in zip(x_values, y_values)]