from ..instance_handle import InstanceHandle
from ..drawing_modes import TriangleMode
from ...geometry import Point
import numpy as np
from ...data_structures import Triangulation, P0, P1, P2

class TriangleInstance(InstanceHandle[Triangulation]):
    def __init__(self, p0 : Point = P0, p1 : Point = P1, p2 : Point = P2):
        self._p0 = p0
        self._p1 = p1
        self._p2 = p2
        self._drawing_mode = TriangleMode()
        self._instance : Triangulation = Triangulation(p0,p1,p2)
        self._drawing_mode.set_instance(self._instance)
        super().__init__(self._instance, self._drawing_mode, 10)
        
    def add_point(self, point: Point) -> bool:
        return self._instance.insert_point(point) is not None

    def clear(self):
        self._instance.reset(self._p0, self._p1, self._p2)

    def size(self) -> int:
        if self._instance is None:
            return 0
        return len(self._instance.edges_as_points()) / 2

    @staticmethod
    def extract_points_from_raw_instance(instance: Triangulation) -> list[Point]:
        if instance is None:
            return []
        return instance.edges_as_points()

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        x_values = np.clip(np.random.normal(0.5 * max_x, 0.15 * max_x, number), 0.05 * max_x, 0.95 * max_x)
        y_values = np.clip(np.random.normal(0.5 * max_y, 0.15 * max_y, number), 0.05 * max_y, 0.95 * max_y)
        return [Point(x, y) for x, y in zip(x_values, y_values)]