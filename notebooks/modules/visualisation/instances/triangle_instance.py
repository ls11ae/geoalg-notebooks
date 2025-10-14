from typing import override

from ...geometry import Point, PointList
from ...data_structures import Triangulation
from ..instance_handle import InstanceHandle
from ..drawing_modes import TriangleMode


class TriangleInstance(InstanceHandle[Triangulation]):
    def __init__(self, p0 : Point, p1 : Point, p2 : Point):
        self._drawing_mode = TriangleMode(p0,p1,p2)
        self._instance : Triangulation = Triangulation(p0,p1,p2)
        super().__init__(self._instance, self._drawing_mode, 10)

    @override
    def add_point(self, point: Point) -> Point | None:
        vertex = self._instance.insert_point(point)
        if vertex is None:
            return None
        print(str(len(vertex.outgoing_edges())))
        return PointList(vertex.point.x, vertex.point.y, [e.destination.point for e in vertex.outgoing_edges()], 0)

    @override
    def clear(self):
        outer_points = self._instance.outer_points
        self._instance = Triangulation(outer_points[0], outer_points[1], outer_points[2])
        self._drawing_mode.outer_triangle_drawn = False

    @override
    def size(self) -> int:
        if self._instance is None:
            return 0
        return self._instance.number_of_vertices

    @staticmethod
    @override
    def extract_points_from_raw_instance(instance: Triangulation) -> list[Point]:
        if instance is None:
            return []
        return instance.to_points()

    @override
    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        self._drawing_mode.outer_triangle_drawn = False
        return TriangleInstance.generate_random_points_uniform(max_x, max_y, number)