from typing import Optional

from ...data_structures import DoublyConnectedSimplePolygon
from ...geometry import Point
from ..drawing import DrawingMode
from ..drawing_modes import PolygonMode
from ..instance_handle import InstanceHandle

class SimplePolygonInstance(InstanceHandle[DoublyConnectedSimplePolygon]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = PolygonMode(mark_closing_edge = True, draw_interior = False, point_radius = 3)
        super().__init__(DoublyConnectedSimplePolygon(), drawing_mode, 100)

    def add_point(self, point: Point) -> bool:
        try:
            self._instance.add_vertex(point)
        except Exception:
            return False
        return True

    def clear(self):
        self._instance.clear()

    def size(self) -> int:
        return len(self._instance)

    @staticmethod
    def extract_points_from_raw_instance(instance: DoublyConnectedSimplePolygon) -> list[Point]:
        return [vertex.point for vertex in instance.vertices()]

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        while True:
            points = SimplePolygonInstance.generate_random_points_uniform(max_x, max_y, number)
            try:
                polygon = DoublyConnectedSimplePolygon.try_from_unordered_points(points)
            except Exception:
                continue
            return self.extract_points_from_raw_instance(polygon)