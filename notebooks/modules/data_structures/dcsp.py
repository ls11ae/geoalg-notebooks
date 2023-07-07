from __future__ import annotations
import copy
from itertools import chain
from typing import Iterable, Iterator, Optional

from ..geometry import LineSegment, Orientation, Point
from .objects import Vertex, HalfEdge

class DoublyConnectedSimplePolygon:
    def __init__(self, boundary_path: Iterable[Point] = []):
        self.clear()
        for point in boundary_path:
            self.add_vertex(point)

    @classmethod
    def try_from_unordered_points(cls, points: Iterable[Point]) -> DoublyConnectedSimplePolygon:
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

        return DoublyConnectedSimplePolygon(path)

    def clear(self):
        self._topmost_vertex: Optional[Vertex] = None
        self._closing_edge: Optional[HalfEdge] = None
        self._is_reversed: bool = False
        self._has_diagonals: bool = False
        self._number_of_vertices: int = 0

    def find_edge(self, point_from: Point, point_to: Point) -> HalfEdge:
        vertex = self.find_vertex(point_from)
        if vertex == None:
            return None
        for edge in vertex.outgoing_edges():
            if edge.destination.point is point_to:
                return edge
        return None    
                

    def find_vertex(self, point: Point) -> Optional[Vertex]:
        for vertex in self.vertices_acw():
            if vertex.point is point:
                return vertex
        return None

    @property
    def topmost_vertex(self) -> Optional[Vertex]:
        return self._topmost_vertex

    def vertices_acw(self) -> Iterator[Vertex]:
        """This traverses the vertices in anticlockwise order, starting at the topmost vertex."""
        if self._closing_edge is None:
            return

        yield self._topmost_vertex
        edge = self._topmost_vertex._edge
        while edge.destination is not self._topmost_vertex:
            yield edge.destination
            edge = edge.destination._edge

    def vertices(self) -> Iterator[Vertex]:
        """This traverses the vertices in the order they were added."""
        if self._closing_edge is None:
            return

        yield self._closing_edge.destination
        edge = self._closing_edge._next if self._is_reversed else self._closing_edge.destination._edge
        while edge is not self._closing_edge:
            yield edge.destination
            edge = edge._next if self._is_reversed else edge.destination._edge

    def has_diagonals(self) -> bool:
        return self._has_diagonals

    def is_simple(self, final_vertex_point: Optional[Point] = None) -> bool:
        if self._number_of_vertices + int(final_vertex_point is not None) < 3:
            return False

        point_iterator = chain(
            (vertex.point for vertex in self.vertices()),
            (final_vertex_point or self._closing_edge.destination._point,)
        )

        line_segments: list[LineSegment] = []
        point = next(point_iterator, None)
        next_point = next(point_iterator, None)
        while next_point is not None:
            if point == next_point:
                return False
            line_segments.append(LineSegment(point, next_point))
            point = next_point
            next_point = next(point_iterator, None)

        if final_vertex_point is None or self._number_of_vertices == 2:
            if isinstance(line_segments[-1].intersection(line_segments[0]), LineSegment):
                return False
        else:
            if line_segments[-1].intersection(line_segments[0]) is not None:
                return False

        for segment in line_segments[1:-2]:
            if line_segments[-1].intersection(segment) is not None:
                return False

        return not isinstance(line_segments[-1].intersection(line_segments[-2]), LineSegment)

    def add_vertex(self, point: Point) -> Vertex:
        if self._has_diagonals:
            raise RuntimeError("Can't add vertex because the polygon already has a diagonal.")
        elif (self._number_of_vertices == 1 and point == self._topmost_vertex._point) or \
        (self._number_of_vertices >= 2 and not self.is_simple(point)):
            raise ValueError(f"Can't add vertex at point {point} because it would break polygon simplicity.")

        vertex = Vertex(point)
        if self._number_of_vertices == 0:
            self._topmost_vertex = vertex
            self._closing_edge = vertex._edge
        else:
            if vertex.y > self._topmost_vertex.y or (vertex.y == self._topmost_vertex.y and \
            vertex.x < self._topmost_vertex.x):
                self._topmost_vertex = vertex
            self._setup_edges_for_new_vertex(vertex)

        self._number_of_vertices += 1
        if self._number_of_vertices >= 3:
            topmost_orientation = self._topmost_vertex.point.orientation(
                self._topmost_vertex._edge._prev._origin._point,
                self._topmost_vertex._edge._next._origin._point
            )
            if topmost_orientation is not Orientation.RIGHT:
                self._reverse_orientation()

        return vertex

    def _setup_edges_for_new_vertex(self, vertex: Vertex):
        old_closing_edge = self._closing_edge
        old_closing_edge_twin = self._closing_edge._twin
        if self._number_of_vertices == 2:
            old_closing_edge = copy.copy(old_closing_edge)
            old_closing_edge_twin = copy.copy(old_closing_edge_twin)
            old_closing_edge._origin._edge = old_closing_edge
            old_closing_edge._set_prev(self._closing_edge._twin)
            old_closing_edge_twin._set_prev(self._closing_edge)

        closing_edge, converse_edge = vertex._edge, HalfEdge(vertex)
        if self._is_reversed:
            closing_edge, converse_edge = converse_edge, closing_edge
        converse_edge._set_twin(old_closing_edge)
        closing_edge._set_twin(old_closing_edge_twin)
        converse_edge._set_next(old_closing_edge_twin._next)
        closing_edge._set_next(old_closing_edge._next)
        converse_edge._set_prev(old_closing_edge_twin)
        closing_edge._set_prev(old_closing_edge)

        self._closing_edge = closing_edge

    def _reverse_orientation(self):
        self._topmost_vertex._edge = self._topmost_vertex._edge._prev._twin
        vertex = self._topmost_vertex._edge.destination
        while vertex is not self._topmost_vertex:
            vertex._edge = vertex._edge._prev._twin
            vertex = vertex._edge.destination

        self._is_reversed = not self._is_reversed

    # TODO: Maybe introduce a bool parameter for toggling the mentionend checks?
    def add_diagonal(self, connection_edge1: HalfEdge, connection_edge2: HalfEdge) -> HalfEdge:
        """This operation omits many checks so that it can run in asymptotically constant time.

        In order to uphold all invariants of the data structure, the caller needs to ensure that:
        - The connection half-edges are part of the polygon this method is called on.
        - The connection half-edges bound the same incident face, which is the polygon interior or a subset thereof.
        - The diagonal, i.e. the line segment between the connection half-edge origins, is contained in the polygon."""
        vertex1 = connection_edge1._origin
        vertex2 = connection_edge2._origin
        if vertex1 is vertex2 or vertex1._edge.destination is vertex2 or vertex2._edge.destination is vertex1:
            raise ValueError(f"Can't add a diagonal between same or adjacent vertices {vertex1} and {vertex2}.")

        diagonal1 = HalfEdge(vertex1)
        diagonal2 = HalfEdge(vertex2)
        diagonal1._set_twin(diagonal2)
        diagonal1._set_prev(connection_edge1._prev)
        diagonal2._set_prev(connection_edge2._prev)
        diagonal1._set_next(connection_edge2)
        diagonal2._set_next(connection_edge1)

        self._has_diagonals = True

        return diagonal1

    def __len__(self) -> int:
        return self._number_of_vertices
