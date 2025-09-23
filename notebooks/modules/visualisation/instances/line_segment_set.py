from typing import Optional
from itertools import chain
import numpy as np

from ...geometry import Point, LineSegment
from ..drawing import DrawingMode
from ..drawing_modes import LineSegmentsMode
from ..instance_handle import InstanceHandle

class LineSegmentSetInstance(InstanceHandle[set[LineSegment]]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = LineSegmentsMode(point_radius = 3)
        super().__init__(set(), drawing_mode, 500)
        self._cached_point: Optional[Point] = None

    def add_point(self, point: Point) -> bool:
        if self._cached_point is None:
            self._cached_point = point
            return True
        elif self._cached_point == point:
            return False

        line_segment = LineSegment(self._cached_point, point)
        if line_segment in self._instance:
            return False
        self._instance.add(line_segment)
        self._cached_point = None

        return True

    def clear(self):
        self._instance.clear()
        self._cached_point = None

    def size(self) -> int:
        return len(self._instance)

    @staticmethod
    def extract_points_from_raw_instance(instance: set[LineSegment]) -> list[Point]:
        return list(chain.from_iterable((segment.upper, segment.lower) for segment in instance))

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        #this might look nicer
        #if number % 2 != 0:
        #    number = number + 1
        #return LineSegmentSetInstance.generate_random_points_uniform(max_x, max_y, number)

        points: list[Point] = []
        for point in LineSegmentSetInstance.generate_random_points_uniform(max_x, max_y, number // 2):
            points.append(point)
            #generate second point nearby
            scale = np.random.uniform(0.01, 0.05)
            x = np.clip(np.random.normal(point.x, scale * max_x), 0.05 * max_x, 0.95 * max_x)
            y = np.clip(np.random.normal(point.y, scale * max_y), 0.05 * max_y, 0.95 * max_y)
            points.append(Point(x, y))

        if number % 2 == 1:
            points.extend(LineSegmentSetInstance.generate_random_points_uniform(max_x, max_y, 1))
        return points
