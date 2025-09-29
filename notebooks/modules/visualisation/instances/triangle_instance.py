from typing import override

from ...geometry import Point
from ...data_structures import Triangulation, P0, P1, P2
from ..instance_handle import InstanceHandle
from ..drawing_modes import TriangleMode


class TriangleInstance(InstanceHandle[Triangulation]):
    def __init__(self, p0 : Point = P0, p1 : Point = P1, p2 : Point = P2):
        self._p0 = p0
        self._p1 = p1
        self._p2 = p2
        self._drawing_mode = TriangleMode()
        self._instance : Triangulation = Triangulation(p0,p1,p2)
        self._drawing_mode.set_instance(self._instance)
        super().__init__(self._instance, self._drawing_mode, 10)

    @override
    def add_point(self, point: Point) -> Point | None:
        return self._instance.insert_point(point).point

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
        return TriangleInstance.generate_random_points_uniform(max_x, max_y, number)