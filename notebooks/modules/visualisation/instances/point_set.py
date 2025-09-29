from typing import Optional, override

from ...geometry import Point
from ..drawing import DrawingMode
from ..drawing_modes import PointsMode
from ..instance_handle import InstanceHandle

class PointSetInstance(InstanceHandle[set[Point]]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = PointsMode()
        super().__init__(set(), drawing_mode, 250)

    @override
    def add_point(self, point: Point) -> Point | None:
        if point in self._instance:
            return None
        self._instance.add(point)
        return point

    @override
    def clear(self):
        self._instance.clear()

    @override
    def size(self) -> int:
        return len(self._instance)

    @staticmethod
    @override
    def extract_points_from_raw_instance(instance: set[Point]) -> list[Point]:
        return list(instance)

    @override
    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        return PointSetInstance.generate_random_points_gaussian(max_x, max_y, number)