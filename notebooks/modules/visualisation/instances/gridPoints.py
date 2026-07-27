from typing import Optional, override

from prometheus_client import delete_from_gateway

from ...geometry import Point
from ..drawing import DrawingMode
from ..drawing_modes import PointsMode
from ..instance_handle import InstanceHandle

class GridPointInstance(InstanceHandle[set[Point]]):
    def __init__(self, origin : Point, x_step_size : float, y_step_size : float, drawing_mode: Optional[DrawingMode] = None):
        self._random_points_mode = 0
        self._origin = origin
        self._x_step_size = x_step_size
        self._y_step_size = y_step_size
        if drawing_mode is None:
            drawing_mode = PointsMode()
        super().__init__(set(), drawing_mode, 10)

    def _get_nearest_gridpoint(self, point : Point) -> Point:
        x_dist = point.x - self._origin.x
        y_dist = point.y - self._origin.y
        x_steps = round(x_dist / self._x_step_size)
        y_steps = round(y_dist / self._y_step_size)
        return Point(self._origin.x + x_steps * self._x_step_size, self._origin.y + y_steps * self._y_step_size)

    @override
    def add_point(self, point: Point) -> Point | None:
        nearest_gridpoint = self._get_nearest_gridpoint(point)
        if nearest_gridpoint in self._instance:
            return None
        self._instance.add(nearest_gridpoint)
        return nearest_gridpoint

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
        return GridPointInstance.generate_random_points_uniform(max_x, max_y, number)