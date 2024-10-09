from __future__ import annotations
from typing import Iterable

from ..geometry import LineSegment, Orientation as ORT, Point, EPSILON

class Vertex:
    """ A vertex for the DCEL """
    def __init__(self, point: Point):
        self._point = point
        self._edge: HalfEdge = HalfEdge(self)

    def outgoing_edges(self) -> Iterable[HalfEdge]:
        outgoing_edges = []
        outgoing_edge = self.edge
        if outgoing_edge.destination == self:  # single vertex
            return []
        outgoing_edges.append(outgoing_edge)  # at least one outgoing edge
        outgoing_edge = outgoing_edge.twin.next
        while outgoing_edge != self.edge:
            outgoing_edges.append(outgoing_edge)
            outgoing_edge = outgoing_edge.twin.next
        return outgoing_edges

    #outgoing and ingoing edges
    def incident_edges(self) -> Iterable[HalfEdge]:
        incident_edges = []
        for out_edge in self.outgoing_edges():
            incident_edges.append(out_edge)
            incident_edges.append(out_edge.twin)
        return incident_edges

    @property
    def point(self) -> Point:
        return self._point

    @property
    def x(self) -> float:
        return self._point.x

    @property
    def y(self) -> float:
        return self._point.y

    @property
    def edge(self) -> HalfEdge:
        return self._edge

    def __repr__(self) -> str:
        return f"Vertex@{self._point}"

class HalfEdge:
    """ A halfedge defined by an origin and twin, previous and next halfedges. """
    def __init__(self, origin: Vertex):
        self._origin = origin
        self._twin: HalfEdge = self
        self._prev: HalfEdge = self
        self._next: HalfEdge = self
        self._incident_face = None

    def cycle(self) -> Iterable[HalfEdge]:
        cycle = [self]
        next_edge = self.next
        while next_edge != self:
            cycle.append(next_edge)
            next_edge = next_edge.next
        return cycle
    
    def vertex_on_cycle(self, vertex: Vertex) -> bool:
        return vertex in [edge.origin for edge in self.cycle()]
    
    def update_face_in_cycle(self, face: Face):
        for edge in self.cycle():
            edge.incident_face = face

    # Determines whether the cycle starting at a given edge is clockwise using the shoelace (trapezoid) formula
    def is_cycle_clockwise(self, epsilon: float = EPSILON) -> bool:
        a = float(0)
        for edge in self.cycle():
            a += (edge.origin.point.y + edge.destination.point.y) * (edge.origin.point.x - edge.destination.point.x)
        return a < -epsilon

    @property
    def origin(self) -> Vertex:
        return self._origin

    @property
    def destination(self) -> Vertex:
        return self._twin._origin

    @property
    def upper_and_lower(self) -> tuple[Vertex, Vertex]:
        p, q = self._origin, self.destination
        if p.y > q.y or (p.y == q.y and p.x < q.x):
            return p, q
        else:
            return q, p
    
    @property
    def left_and_right(self) -> tuple[Vertex, Vertex]:
        p, q = self._origin, self.destination
        if p.x < q.x or (p.x == q.x and p.y < q.y):
            return p, q
        else:
            return q, p

    @property
    def left(self) -> Vertex:
        return self.left_and_right[0]

    @property
    def right(self) -> Vertex:
        return self.left_and_right[1]    

    @property
    def twin(self) -> HalfEdge:
        return self._twin

    @property
    def prev(self) -> HalfEdge:
        return self._prev

    @property
    def next(self) -> HalfEdge:
        return self._next
    
    @property
    def incident_face(self) -> Face:
        return self._incident_face
    
    @property
    def length(self) -> float:
        return self.origin.point.distance(self.destination.point)

    @incident_face.setter
    def incident_face(self, incident_face):
        self._incident_face = incident_face

    def _set_twin(self, twin: HalfEdge):
        self._twin = twin
        twin._twin = self

    def _set_prev(self, prev: HalfEdge):
        self._prev = prev
        prev._next = self

    def _set_next(self, next: HalfEdge):
        self._next = next
        next._prev = self

    def __repr__(self) -> str:
        return f"Edge@{self._origin._point}->{self.destination._point}"
    
class Face:
    """ Face with inner components """
    # TODO: maybe add additional methods (see ruler of the plane): polygon, polygonwithoutholes, innerpolygons, area, bounding-box
    def __init__(self, outer_component: HalfEdge):
        self._outer_component: HalfEdge = outer_component
        self._is_outer = False
        self._inner_components: list[HalfEdge] = []
    
    @property
    def outer_component(self) -> HalfEdge:
        return self._outer_component
    
    @outer_component.setter
    def outer_component(self, edge):
        self._outer_component = edge
    
    @property
    def is_outer(self) -> bool:
        return self._is_outer
    
    @property
    def inner_components(self) -> list[HalfEdge]:
        return self._inner_components
    
    @inner_components.setter
    def inner_components(self, inner_components: Iterable[HalfEdge]):
        self._inner_components = list(inner_components)
    
    def outer_points(self) -> Iterable[Point]:
        return [edge.origin.point for edge in self.outer_half_edges()]
    
    def outer_vertices(self) -> Iterable[Vertex]:
        return [edge.origin for edge in self.outer_half_edges()]
    
    def outer_half_edges(self) -> Iterable[HalfEdge]:
        if self.outer_component == None:
            return []
        outer_edges = [self._outer_component]
        current_edge = self.outer_component.next
        while current_edge != self.outer_component:
            outer_edges.append(current_edge)
            current_edge = current_edge.next
        return outer_edges
    
    def inner_half_edges(self) -> Iterable[HalfEdge]:
        inner_half_edges = []
        for component in self.inner_components:
            inner_half_edges.extend(component.cycle())
        return inner_half_edges

    def contains(self, search_point: Point) -> bool:
        # Ray Casting Algorithm
        inside = False
        ray = LineSegment(Point(-EPSILON, search_point.y), search_point)
        for edge in self.outer_half_edges():
            ls = LineSegment(edge.origin.point, edge.destination.point)
            intersection = ls.intersection(ray)
            if isinstance(intersection, Point) and \
                    (intersection != edge.origin.point or edge.destination.point.y < search_point.y) and \
                    (intersection != edge.destination.point or edge.origin.point.y < search_point.y):
                inside = not inside
        return inside

    def is_convex(self) -> bool:
        if len(self.outer_vertices()) < 3:
            raise Exception("Convexitivity is illdefined for polygons of 2 or less vertices.")

        for edge in self.outer_half_edges():
            if edge.next.destination.point.orientation(edge.origin.point, edge.destination.point) == ORT.RIGHT:
                return False
        return True

    def __repr__(self) -> str:
        if self.is_outer:
            return f"Outer face with inner components {self.inner_components}"
        else:
            return f"Face with outer cycle {self.outer_component.cycle()} and inner components {self.inner_components}"
