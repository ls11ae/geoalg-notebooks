from typing import Optional

from ...data_structures import DoublyConnectedEdgeList
from ...geometry import Point, PointReference
from ..drawing import DrawingMode
from ..drawing_modes import DCELMode
import numpy as np

from ..instance_handle import InstanceHandle


class DCELInstance(InstanceHandle[DoublyConnectedEdgeList]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None, drawing_epsilon: float = 5):
        if drawing_mode is None:
            drawing_mode = DCELMode(vertex_radius = 3)
        self._drawing_epsilon = drawing_epsilon
        self._last_added_point = None
        self._dcel = self._instance  # This is so that that DCELInstance can be used by the PointLocationInstance where the dcel is not the instance itself
        super().__init__(DoublyConnectedEdgeList(), drawing_mode, 20)

    def add_point(self, point: Point) -> bool:
        # Check if point is already in the DCEL
        is_new_point = True
        for instance_point in self._dcel.points:
            if instance_point.close_to(point, epsilon = self._drawing_epsilon):
                is_new_point = False
                point = instance_point
                break

        # Add point (if necessary)
        if is_new_point:
            if isinstance(point, PointReference):
                self._dcel.add_vertex(point.container[point.position])
                # Add edges from Point-Reference-Container
                for i, neighbor in enumerate(point.container):
                    if i == point.position:
                        continue
                    if neighbor not in [vertex.point for vertex in self._dcel.vertices]:
                        continue
                    found = False
                    for edge in self._dcel.edges:
                        if edge.origin == point and edge.destination == neighbor:
                            found = True
                            break
                    if not found:
                        self._dcel.add_edge_by_points(point, neighbor)
            else:
                self._dcel.add_vertex(point)

        # Add edge from last clicked point
        if self._last_added_point is not None and self._last_added_point != point:
            self._dcel.add_edge_by_points(self._last_added_point, point)
            point = PointReference([point, self._last_added_point], 0)
            self._last_added_point = None
        elif not is_new_point:
            self._last_added_point = point

        return is_new_point, point

    def clear(self):
        self._instance.clear()
        self._last_added_point = None

    def size(self) -> int:
        return self._dcel.number_of_vertices

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
    
    def generate_random_points(self, max_x: float, max_y: float, number: int, min_distance = None) -> list[PointReference]:
        while True:
            # grid pattern with min distance up/down and left/right = 1
            if min_distance is None:
                min_distance = self._drawing_epsilon
            points = super().generate_random_points(max_x/min_distance, max_y/min_distance, number)

            points = [Point(np.round(point.x, 0), np.round(point.y, 0)) for point in points]
            points = [Point(point.x*min_distance, point.y*min_distance) for point in points]

            if len(points) != len(set(points)):  # Duplicate point(s)
                continue

            # 2-OPT path as in DCSP
            path = list(points)
            n = len(path)
            found_improvement = True
            while found_improvement:
                found_improvement = False
                for i in range(0, n - 1):
                    for j in range(i + 1, n):
                        subpath_distances = path[i].distance(path[j]) + path[i + 1].distance(path[(j + 1) % n])
                        neighbour_distances = path[i].distance(path[i + 1]) + path[j].distance(path[(j + 1) % n])
                        if subpath_distances < neighbour_distances:
                            path[i + 1:j + 1] = reversed(path[i + 1:j + 1])
                            found_improvement = True
            
            circle = [(i, i + 1) for i in range(n - 1)]
            if len(circle) > 1:
                circle.append((n - 1, 0))
            try:
                dcel = DoublyConnectedEdgeList(path, circle)
            except Exception():
                continue

            # Add some more edges:
            count = 0
            first  = np.int32(np.random.uniform(0, dcel.number_of_vertices, 1000))
            second = np.int32(np.random.uniform(0, dcel.number_of_vertices, 1000))
            tuple = zip(first, second)
            for tuple in zip(first, second):
                try:
                    if dcel.add_edge(tuple, True):
                        count = count + 1
                        if count >= number / 5:
                            break
                except (RuntimeError, Exception):
                    continue

            return self.extract_points_from_raw_instance(dcel)