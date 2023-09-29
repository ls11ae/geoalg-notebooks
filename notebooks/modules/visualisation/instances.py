from abc import ABC, abstractmethod
from itertools import chain
import time
from typing import Callable, Generic, Optional, TypeVar, Union

from ..geometry.core import GeometricObject, LineSegment, Point, PointReference
from ..data_structures import DoublyConnectedSimplePolygon, DoublyConnectedEdgeList, PointLocation
from .drawing import DrawingMode, LineSegmentsMode, PointsMode, PolygonMode, DCELMode, PointLocationMode

import numpy as np


I = TypeVar("I")

Algorithm = Callable[[I], GeometricObject]

class InstanceHandle(ABC, Generic[I]):
    def __init__(self, instance: I, drawing_mode: DrawingMode):
        self._instance = instance
        self._drawing_mode = drawing_mode

    @property
    def drawing_mode(self) -> DrawingMode:
        return self._drawing_mode

    def run_algorithm(self, algorithm: Algorithm[I]) -> tuple[GeometricObject, float]:
        instance_points = self.extract_points_from_raw_instance(self._instance)

        start_time = time.perf_counter()
        algorithm_output = algorithm(self._instance)
        end_time = time.perf_counter()

        self.clear()
        for point in instance_points:
            self.add_point(point)

        return algorithm_output, 1000 * (end_time - start_time)

    @abstractmethod
    def add_point(self, point: Point) -> Union[bool, tuple[bool, Point]]:
        pass

    @abstractmethod
    def clear(self):
        pass

    @abstractmethod
    def size(self) -> int:
        pass

    @staticmethod
    @abstractmethod
    def extract_points_from_raw_instance(instance: I) -> list[Point] | list[PointReference]:
        pass

    @property
    @abstractmethod
    def default_number_of_random_points(self) -> int:
        pass

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        x_values = np.random.uniform(0.05 * max_x, 0.95 * max_x, number)
        y_values = np.random.uniform(0.05 * max_y, 0.95 * max_y, number)
        return [Point(x, y) for x, y  in zip(x_values, y_values)]


class PointSetInstance(InstanceHandle[set[Point]]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = PointsMode()
        super().__init__(set(), drawing_mode)

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

    @property
    def default_number_of_random_points(self) -> int:
        return 250

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        x_values = np.clip(np.random.normal(0.5 * max_x, 0.15 * max_x, number), 0.05 * max_x, 0.95 * max_x)
        y_values = np.clip(np.random.normal(0.5 * max_y, 0.15 * max_y, number), 0.05 * max_y, 0.95 * max_y)
        return [Point(x, y) for x, y in zip(x_values, y_values)]


class LineSegmentSetInstance(InstanceHandle[set[LineSegment]]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = LineSegmentsMode(vertex_radius = 3)
        super().__init__(set(), drawing_mode)
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

    @property
    def default_number_of_random_points(self) -> int:
        return 500

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


class SimplePolygonInstance(InstanceHandle[DoublyConnectedSimplePolygon]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = PolygonMode(mark_closing_edge = True, draw_interior = False, vertex_radius = 3)
        super().__init__(DoublyConnectedSimplePolygon(), drawing_mode)

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

    @property
    def default_number_of_random_points(self) -> int:
        return 100

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        while True:
            points = super().generate_random_points(max_x, max_y, number)

            try:
                polygon = DoublyConnectedSimplePolygon.try_from_unordered_points(points)
            except Exception:
                continue

            return self.extract_points_from_raw_instance(polygon)

class DCELInstance(InstanceHandle[DoublyConnectedEdgeList]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None, drawing_epsilon: float = 5):
        if drawing_mode is None:
            drawing_mode = DCELMode(vertex_radius = 3)
        self._drawing_epsilon = drawing_epsilon
        self._last_added_point = None
        super().__init__(DoublyConnectedEdgeList(), drawing_mode)

    def add_point(self, point: Point) -> bool:
        # Check if point is already in the DCEL
        is_new_point = True
        for instance_point in self._instance.points:
            if instance_point.close_to(point, epsilon = self._drawing_epsilon):
                print("old point")
                is_new_point = False
                point = instance_point
                break

        # Add point (if necessary)
        if is_new_point:
            if isinstance(point, PointReference):
                self._instance.add_vertex(point.container[point.position])
                # Add edges from Point-Reference-Container
                for i, neighbor in enumerate(point.container):
                    if i == point.position:
                        continue
                    if neighbor not in [vertex.point for vertex in self._instance.vertices]:
                        continue
                    found = False
                    for edge in self._instance.edges:
                        if edge.origin == point and edge.destination == neighbor:
                            found = True
                            break
                    if not found:
                        self._instance.add_edge_by_points(point, neighbor)
            else:
                self._instance.add_vertex(point)

        # Add edge from last clicked point
        if self._last_added_point is not None and self._last_added_point != point:
            self._instance.add_edge_by_points(self._last_added_point, point)
            point = PointReference([point, self._last_added_point], 0)
            self._last_added_point = None
        elif not is_new_point:
            print("Jup")
            self._last_added_point = point

        return is_new_point, point

    def clear(self):
        self._instance.clear()
        self._last_added_point = None

    def size(self) -> int:
        return self._instance.number_of_vertices

    @staticmethod
    def extract_points_from_raw_instance(instance: DoublyConnectedEdgeList) -> list[PointReference]:
        point_list: list[PointReference] = []
        for vertex in instance.vertices:
            neighbors: list[Point] = [vertex.point]  # start with the point itself in the list
            if vertex.edge.destination != vertex:  # at least one neighbor
                neighbors.append(vertex.edge.destination.point)
                edge = vertex.edge.twin.next
                while edge != vertex.edge:  # iterate over all neighbors
                    neighbors.append(edge.destination.point)
                    edge = edge.twin.next
            point_list.append(PointReference(neighbors, 0))
        return point_list

    @property
    def default_number_of_random_points(self) -> int:
        return 20

class PointLocationInstance(InstanceHandle[PointLocation]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None):
        if drawing_mode is None:
            drawing_mode = PointLocationMode(vertex_radius = 3)
        super().__init__(PointLocation(), drawing_mode)
        self._cached_point: Optional[Point] = None

    def add_point(self, point: Point) -> bool:
        if self._cached_point is None:
            self._cached_point = point
            return True
        if self._cached_point == point:
            return False
        
        line_segment = LineSegment(self._cached_point, point)
        if line_segment in self._instance._vertical_decomposition.line_segments:
            return False
        self._instance.insert(line_segment)
        self._cached_point = None

        return True
    
    def clear(self):
        self._instance.clear()
        self._cached_point = None
    
    def size(self) -> int:
        return len(self._instance._vertical_decomposition.line_segments)
    
    @staticmethod
    def extract_points_from_raw_instance(instance: PointLocation) -> list[PointReference]:
        point_list: list[PointReference] = []
        for line_segment in instance._vertical_decomposition.line_segments:
            point_list.append(PointReference([line_segment.left], 0))
            point_list.append(PointReference([line_segment.right], 0))

        for trapezoid in instance._vertical_decomposition.trapezoids:
            for point in point_list:
                if point == trapezoid.left_point or point == trapezoid.right_point:
                    point_above = Point(point.x, trapezoid.top_line_segment.y_from_x(point.x))
                    point_below = Point(point.x, trapezoid.bottom_line_segment.y_from_x(point.x))
                    if len(point.container) == 1:
                        point.container.append(point_above)
                    elif point.container[1].y < point_above.y:
                        point.container[1] = point_above
                    if len(point.container) == 2:
                        point.container.append(point_below)
                    elif point.container[2].y > point_below.y:
                        point.container[2] = point_below
        return point_list

    @property
    def default_number_of_random_points(self) -> int:
        return 20
