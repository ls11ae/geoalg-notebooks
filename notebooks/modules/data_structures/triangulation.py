from __future__ import annotations
import copy
from typing import Iterator, Optional, Any, Callable
from enum import Enum, auto
import numpy as np

# Data structure, geometry and visualisation module imports
from .binary_tree import BinaryTreeDict, Comparator, ComparisonResult as CR
from .objects import HalfEdge, Vertex
from .dcsp import DoublyConnectedSimplePolygon
from ..geometry import PointSequence, Orientation as ORT

# From Notebook 03:

# Recursive Triangulation

def recursive_triangulation(polygon: DoublyConnectedSimplePolygon) -> PointSequence:
    if polygon.has_diagonals():
        raise ValueError("Input polygon already has diagonals.")
    elif not polygon.is_simple():
        raise ValueError("Input polygon isn't simple.")

    diagonal_points = PointSequence()
    representative_edges = [polygon.topmost_vertex.edge]
    while representative_edges:
        leftmost_edge = get_leftmost_edge(representative_edges.pop())
        connection_edges = get_connection_edges(leftmost_edge)
        if connection_edges is not None:
            diagonal = polygon.add_diagonal(connection_edges[0], connection_edges[1])
            diagonal_points.append(diagonal.origin.point)
            diagonal_points.append(diagonal.destination.point)
            representative_edges.append(diagonal)
            representative_edges.append(diagonal.twin)

    return diagonal_points

def get_leftmost_edge(representative_edge: HalfEdge) -> HalfEdge:
    leftmost_edge, leftmost_vertex = representative_edge, representative_edge.origin
    edge = representative_edge.next
    while edge is not representative_edge:
        vertex = edge.origin
        if vertex.x < leftmost_vertex.x or (vertex.x == leftmost_vertex.x and vertex.y < leftmost_vertex.y):
            leftmost_edge, leftmost_vertex = edge, vertex
        edge = edge.next

    return leftmost_edge

def get_connection_edges(leftmost_edge: HalfEdge) -> Optional[tuple[HalfEdge, HalfEdge]]:
    edge = leftmost_edge.next.next
    if edge is leftmost_edge.prev:
        return None

    triangle = (leftmost_edge.prev.origin, leftmost_edge.origin, leftmost_edge.next.origin)
    conflicting_edge, max_coordinate = None, 0.0
    while edge is not leftmost_edge.prev:
        area_coordinates = calculate_area_coordinates(edge.origin, triangle)
        if all(0.0 <= coordinate <= 1.0 for coordinate in area_coordinates):
            if conflicting_edge is None or area_coordinates[1] > max_coordinate:
                conflicting_edge, max_coordinate = edge, area_coordinates[1]
        edge = edge.next

    if conflicting_edge is None:
        return leftmost_edge.prev, leftmost_edge.next
    return leftmost_edge, conflicting_edge

def calculate_area_coordinates(vertex: Vertex, triangle: tuple[Vertex, Vertex, Vertex]) -> tuple[float, float, float]:
    parallelogram_area = calculate_signed_area(triangle[0], triangle[1], triangle[2])
    return (
        calculate_signed_area(vertex, triangle[1], triangle[2]) / parallelogram_area,
        calculate_signed_area(triangle[0], vertex, triangle[2]) / parallelogram_area,
        calculate_signed_area(triangle[0], triangle[1], vertex) / parallelogram_area
    )

def calculate_signed_area(u: Vertex, v: Vertex, w: Vertex) -> float:
    p, q, r = u.point, v.point, w.point
    return (q - p).perp_dot(r - p)

# Montone Triangulation:

class EventQueueComparator(Comparator[Vertex]):
    def compare(self, item: Any, key: Vertex) -> CR:
        if not isinstance(item, Vertex):
            raise TypeError("Only vertices can be compared with event vertices.")
        elif item.point == key.point:
            return CR.MATCH
        elif item.y > key.y or (item.y == key.y and item.x < key.x):
            return CR.BEFORE
        else:
            return CR.AFTER
        
class StatusStructureComparator(Comparator[HalfEdge]):
    def compare(self, item: Any, key: HalfEdge) -> CR:
        if isinstance(item, Vertex):
            return self._compare_vertex_with_edge(item, key)
        elif isinstance(item, HalfEdge):
            return self._compare_edge_with_edge(item, key)
        else:
            raise TypeError("Only vertices and half-edges can be compared with status half-edges.")

    def _compare_vertex_with_edge(self, vertex: Vertex, edge: HalfEdge) -> CR:
        upper, lower = edge.upper_and_lower
        ort = vertex.point.orientation(lower.point, upper.point)
        if ort is ORT.LEFT:
            return CR.BEFORE
        elif ort is ORT.RIGHT:
            return CR.AFTER
        else:
            return CR.MATCH

    def _compare_edge_with_edge(self, edge1: HalfEdge, edge2: HalfEdge) -> CR:
        upper1, lower1 = edge1.upper_and_lower
        upper2, lower2 = edge2.upper_and_lower
        if upper1.point == upper2.point and lower1.point == lower2.point:
            return CR.MATCH
        elif lower2.y <= upper1.y <= upper2.y:
            return self._compare_vertex_with_edge(upper1, edge2)
        elif lower1.y <= upper2.y <= upper1.y:
            upper2_cr = self._compare_vertex_with_edge(upper2, edge1)
            if upper2_cr is CR.BEFORE:
                return CR.AFTER
            elif upper2_cr is CR.AFTER:
                return CR.BEFORE
            else:
                return CR.MATCH
        else:
            raise ValueError(f"The y-ranges of half-edges {edge1} and {edge2} don't intersect.")
        
class VertexType(Enum):
    START = auto()
    END = auto()
    SPLIT = auto()
    MERGE = auto()
    REGULAR = auto()

VT = VertexType

class VertexInfo:
    event_queue_comparator = EventQueueComparator()

    def __init__(self, vertex: Vertex):
        self.incoming_edge: HalfEdge = vertex.edge.prev
        self.outgoing_edge: HalfEdge = vertex.edge
        self.connection_edge: HalfEdge = vertex.edge

        prev_neighbour = self.incoming_edge.origin
        next_neighbour = self.outgoing_edge.destination
        prev_cr = self.event_queue_comparator.compare(prev_neighbour, vertex)
        next_cr = self.event_queue_comparator.compare(next_neighbour, vertex)
        if prev_cr is CR.AFTER and next_cr is CR.AFTER:
            if vertex.point.orientation(prev_neighbour.point, next_neighbour.point) is ORT.RIGHT:
                self.vertex_type = VT.START
            else:
                self.vertex_type = VT.SPLIT
        elif prev_cr is CR.BEFORE and next_cr is CR.BEFORE:
            if vertex.point.orientation(prev_neighbour.point, next_neighbour.point) is ORT.RIGHT:
                self.vertex_type = VT.END
            else:
                self.vertex_type = VT.MERGE
        else:
            self.vertex_type = VT.REGULAR

def monotone_partitioning(polygon: DoublyConnectedSimplePolygon) -> PointSequence:
    return MonotonePartitioning(polygon).partition()[0]

class MonotonePartitioning:
    def __init__(self, polygon: DoublyConnectedSimplePolygon):
        if polygon.has_diagonals():
            raise ValueError("Input polygon already has diagonals.")
        elif not polygon.is_simple():
            raise ValueError("Input polygon isn't simple.")
        self._polygon = polygon

        self._diagonal_points = PointSequence()
        self._representative_edges: list[HalfEdge] = []

        self._status_structure: BinaryTreeDict[HalfEdge, VertexInfo] = BinaryTreeDict(StatusStructureComparator())
        self._event_queue: BinaryTreeDict[Vertex, VertexInfo] = BinaryTreeDict(VertexInfo.event_queue_comparator)

        for vertex in self._polygon.vertices():
            self._event_queue.insert(vertex, VertexInfo(vertex))

    def partition(self) -> tuple[PointSequence, list[HalfEdge]]:
        while not self._event_queue.is_empty():
            event_vertex, event_vertex_info = self._event_queue.pop_first()
            handler_name = f"_handle_{str.lower(event_vertex_info.vertex_type.name)}_vertex"
            handler: Callable[[Vertex, VertexInfo], None] = getattr(self, handler_name)
            handler(event_vertex, event_vertex_info)
            if event_vertex_info.incoming_edge is event_vertex_info.outgoing_edge.prev:
                self._diagonal_points.animate(event_vertex.point)    # Animate point even if no diagonal was added.

        return self._diagonal_points, self._representative_edges

    def _handle_start_vertex(self, _: Vertex, event_vertex_info: VertexInfo):
        self._status_structure.insert(event_vertex_info.outgoing_edge, event_vertex_info)

    def _handle_end_vertex(self, _: Vertex, event_vertex_info: VertexInfo):
        _, inc_helper_info = self._status_structure.delete(event_vertex_info.incoming_edge)
        if inc_helper_info.vertex_type is VT.MERGE:
            diagonal, _ = self._add_diagonal(event_vertex_info, inc_helper_info)
            self._representative_edges.append(diagonal)
        self._representative_edges.append(event_vertex_info.outgoing_edge)

    def _handle_split_vertex(self, event_vertex: Vertex, event_vertex_info: VertexInfo):
        left_status_edge, left_helper_info = self._status_structure.search_predecessor(event_vertex)
        _, new_event_vertex_info = self._add_diagonal(event_vertex_info, left_helper_info)
        self._status_structure.update(left_status_edge, lambda _: new_event_vertex_info)
        self._status_structure.insert(event_vertex_info.outgoing_edge, event_vertex_info)

    def _handle_merge_vertex(self, event_vertex: Vertex, event_vertex_info: VertexInfo):
        _, inc_helper_info = self._status_structure.delete(event_vertex_info.incoming_edge)
        if inc_helper_info.vertex_type is VT.MERGE:
            diagonal, _ = self._add_diagonal(event_vertex_info, inc_helper_info)
            self._representative_edges.append(diagonal)
        left_status_edge, left_helper_info = self._status_structure.search_predecessor(event_vertex)
        if left_helper_info.vertex_type is VT.MERGE:
            diagonal, event_vertex_info = self._add_diagonal(event_vertex_info, left_helper_info)
            self._representative_edges.append(diagonal.twin)
        self._status_structure.update(left_status_edge, lambda _: event_vertex_info)

    def _handle_regular_vertex(self, event_vertex: Vertex, event_vertex_info: VertexInfo):
        is_interior_to_the_right, inc_helper_info = self._status_structure.delete(event_vertex_info.incoming_edge)
        if is_interior_to_the_right:
            if inc_helper_info.vertex_type is VT.MERGE:
                diagonal, _ = self._add_diagonal(event_vertex_info, inc_helper_info)
                self._representative_edges.append(diagonal)
            self._status_structure.insert(event_vertex_info.outgoing_edge, event_vertex_info)
        else:
            left_status_edge, left_helper_info = self._status_structure.search_predecessor(event_vertex)
            if left_helper_info.vertex_type is VT.MERGE:
                diagonal, event_vertex_info = self._add_diagonal(event_vertex_info, left_helper_info)
                self._representative_edges.append(diagonal.twin)
            self._status_structure.update(left_status_edge, lambda _: event_vertex_info)

    def _add_diagonal(self, event_vertex_info: VertexInfo, helper_info: VertexInfo) -> tuple[HalfEdge, VertexInfo]:
        diagonal = self._polygon.add_diagonal(event_vertex_info.connection_edge, helper_info.connection_edge)
        self._diagonal_points.append(diagonal.origin.point)
        self._diagonal_points.append(diagonal.destination.point)
        new_event_vertex_info = copy.copy(event_vertex_info)
        new_event_vertex_info.connection_edge = diagonal
        return diagonal, new_event_vertex_info
    
def monotone_triangulation(polygon: DoublyConnectedSimplePolygon) -> PointSequence:
    diagonal_points, representative_edges = MonotonePartitioning(polygon).partition()
    supporter = MonotoneSupporter(polygon, diagonal_points)

    for edge_sequence in supporter.get_edge_sequences(representative_edges):
        stack = edge_sequence[0:2]

        for current_edge, current_ort in edge_sequence[2:-1]:
            connection_edge = current_edge
            popped_edge, popped_ort = stack.pop()
            if current_ort is not popped_ort:
                cached_edge, cached_ort = popped_edge, popped_ort
                while stack:
                    connection_edge = supporter.add_diagonal(connection_edge, popped_edge, popped_ort)
                    popped_edge, popped_ort = stack.pop()
            else:
                current_point = current_edge.origin.point
                while stack:
                    ort = popped_edge.origin.point.orientation(current_point, stack[-1][0].origin.point)
                    if ort is not current_ort:
                        break
                    popped_edge, popped_ort = stack.pop()
                    connection_edge = supporter.add_diagonal(connection_edge, popped_edge, popped_ort)
                cached_edge, cached_ort = popped_edge, popped_ort
            if current_ort is ORT.LEFT:
                stack.append((current_edge.prev, cached_ort))
                stack.append((current_edge, current_ort))
            else:
                stack.append((cached_edge, cached_ort))
                stack.append((cached_edge.prev, current_ort))

        connection_edge = edge_sequence[-1][0]
        stack.pop()
        popped_edge, popped_ort = stack.pop()
        while stack:
            connection_edge = supporter.add_diagonal(connection_edge, popped_edge, popped_ort)
            popped_edge, popped_ort = stack.pop()

    return diagonal_points

class MonotoneSupporter:
    def __init__(self, polygon: DoublyConnectedSimplePolygon, diagonal_points: PointSequence):
        self._polygon = polygon
        self._diagonal_points = diagonal_points
        self._diagonal_points.reset_animations()    # Remove animations of points with no diagonal.

    def get_edge_sequences(self, representative_edges: list[HalfEdge]) -> Iterator[list[tuple[HalfEdge, ORT]]]:
        for representative_edge in representative_edges:
            topmost_edge = representative_edge
            edge = representative_edge.next
            while edge is not representative_edge:
                if VertexInfo.event_queue_comparator.compare(edge.origin, topmost_edge.origin) is CR.BEFORE:
                    topmost_edge = edge
                edge = edge.next

            edge_sequence: list[tuple[HalfEdge, ORT]] = [(topmost_edge, ORT.LEFT)]
            left_chain_edge = topmost_edge.next
            right_chain_edge = topmost_edge.prev
            while True:
                cr = VertexInfo.event_queue_comparator.compare(left_chain_edge.origin, right_chain_edge.origin)
                if cr is CR.BEFORE:
                    edge_sequence.append((left_chain_edge, ORT.LEFT))
                    left_chain_edge = left_chain_edge.next
                else:
                    edge_sequence.append((right_chain_edge, ORT.RIGHT))
                    if cr is CR.MATCH:
                        break
                    right_chain_edge = right_chain_edge.prev

            yield edge_sequence

    def add_diagonal(self, connection_edge: HalfEdge, popped_edge: HalfEdge, popped_ort: ORT) -> HalfEdge:
        diagonal = self._polygon.add_diagonal(connection_edge, popped_edge)
        self._diagonal_points.append(diagonal.origin.point)
        self._diagonal_points.append(diagonal.destination.point)

        if popped_ort is ORT.LEFT:
            return connection_edge
        return diagonal