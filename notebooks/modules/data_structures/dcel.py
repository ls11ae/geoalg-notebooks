from __future__ import annotations
import copy
from itertools import chain
from typing import Iterable, Iterator, Optional, Tuple
import numpy as np

from ..geometry import LineSegment, Orientation as ORT, Point

class Vertex:
    def __init__(self, point: Point):
        self._point = point
        self._edge: HalfEdge = HalfEdge(self)

    def outgoing_edges(self) -> Iterable[HalfEdge]:
        outgoing_edges = []
        outgoing_edge = self.edge
        if outgoing_edge.destination == self: #single vertex
            return []
        outgoing_edges.append(outgoing_edge) #at least one outgoing edge
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
    """ Simple face without inner components """
    #TODO: add inner components
    def __init__(self, outer_component: HalfEdge):
        self._outer_component: HalfEdge = outer_component
        self._is_outer = False
    
    @property
    def outer_component(self):
        return self._outer_component
    
    @property
    def is_outer(self):
        return self._is_outer
    
    # TODO maybe add additional methods (see ruler of the plane): outervertices, outerhalfedges, outerpoints, (innercomponents, innerhalfedges, innerpolygons,) polygon, polygonwithourholes, area, contains, boundingbox, tostring

class DoublyConnectedEdgeList:
    """ Simple DCEL without inner components """
    # TODO: Add additional methods (see ruler of the plane):
    # boundingbox, (init with boundingbox, init with linesegments and bounding box,)
    # addvertexinedge, addsegment, addline, 
    # IMPROVE: AddEdge, splitface, getsplittingface, getcontainingface, (addface,)
    # PRIVATE: addvertexinedgechain, fixinnercomponents, iscycleclockwise, updatefaceincycle, onedge, assertwellformed
    def __init__(self, points: Iterable[Point] = [], edges: Iterable[Tuple[int, int]] = []):
        self.clear()
        for point in points:
            self.add_vertex(point)
        for edge in edges:
            self.add_edge(edge)


    def add_vertex(self, point: Point) -> Vertex:
        #TODO: check on edge
        if point in [vertex.point for vertex in self._vertices]:
            return None
        newVertex: Vertex = Vertex(point)
        self._vertices.append(newVertex)
        if len(self._vertices) > 0:
            self._start_vertex = self._vertices[0]
        return newVertex

    def add_edge(self, edge: Tuple[int, int]) -> None:
        if (edge[0] >= self.number_of_vertices() or edge[0] < 0
            or edge[1] >= self.number_of_vertices() or edge[1] < 0): # Impossible indicies
            return
        vertex_1 = self._vertices[edge[0]]
        vertex_2 = self._vertices[edge[1]]
        half_edge_1 = None
        half_edge_2 = None
        if vertex_1.edge == vertex_1.edge.twin: #single vertex
            half_edge_1 = vertex_1.edge
        else:
            half_edge_1 = HalfEdge(vertex_1)
            self._edges.append(half_edge_1)
        if vertex_2.edge == vertex_2.edge.twin: #single vertex
            half_edge_2 = vertex_2.edge
        else:
            half_edge_2 = HalfEdge(vertex_2)
            self._edges.append(half_edge_2)

        # Handle faces
        num_out_edges_1 = len(vertex_1.outgoing_edges())
        num_out_edges_2 = len(vertex_2.outgoing_edges())
        face_1, face_2 = None, None
        if num_out_edges_1 != 0 and num_out_edges_2 != 0:
            pass #TODO
        elif num_out_edges_1 != 0:
            pass #TODO
        elif num_out_edges_2 != 0:
            pass #TODO
        else:
            pass #TODO
        
        if face_1 != face_2:
            raise RuntimeError("Vertices do not lie in the same face")

        # Find correct order around vertex_1
        search_edge = vertex_1.edge.twin
        if vertex_1.edge != vertex_1.edge.twin and vertex_1.edge.twin != vertex_1.edge.prev: # >1 adjacent vertices
            while not ((vertex_2.point.orientation(search_edge.origin.point, search_edge.destination.point) == ORT.LEFT
                    and (vertex_2.point.orientation(search_edge.next.origin.point, search_edge.next.destination.point) == ORT.LEFT
                    or search_edge.next.destination.point.orientation(search_edge.origin.point, search_edge.destination.point) == ORT.RIGHT))
                    or (vertex_2.point.orientation(search_edge.next.origin.point, search_edge.next.destination.point) == ORT.LEFT
                    and search_edge.origin.point.orientation(search_edge.next.origin.point, search_edge.next.destination.point) == ORT.RIGHT)):
                search_edge = search_edge.next.twin
                if search_edge == vertex_1.edge.twin:
                    raise Exception(f"Could not find a suitable edge while inserting {edge}")
        
        # Find correct order around vertex_2
        search_edge2 = vertex_2.edge.twin
        if vertex_2.edge != vertex_2.edge.twin and vertex_2.edge.twin != vertex_2.edge.prev: # >1 adjacent vertices
            while not ((vertex_1.point.orientation(search_edge2.origin.point, search_edge2.destination.point) == ORT.LEFT
                    and (vertex_1.point.orientation(search_edge2.next.origin.point, search_edge2.next.destination.point) == ORT.LEFT
                    or search_edge2.next.destination.point.orientation(search_edge2.origin.point, search_edge2.destination.point) == ORT.RIGHT))
                    or (vertex_1.point.orientation(search_edge2.next.origin.point, search_edge2.next.destination.point) == ORT.LEFT
                    and search_edge2.origin.point.orientation(search_edge2.next.origin.point, search_edge2.next.destination.point) == ORT.RIGHT)):
                search_edge2 = search_edge2.next.twin
                if search_edge2 == vertex_2.edge.twin:
                    raise Exception(f"Could not find a suitable edge while inserting {edge}")
                
        # Set edge pointers
        half_edge_1._incident_face = face_1
        half_edge_2._incident_face = face_1

        half_edge_1._set_twin(half_edge_2)

        old_s1_next = search_edge.next
        old_s2_next = search_edge2.next

        search_edge._set_next(half_edge_1)
        search_edge2._set_next(half_edge_2)
        
        half_edge_1._set_next(old_s2_next)
        half_edge_2._set_next(old_s1_next)

        # Add fix for inner components here

    def clear(self):
        self._start_vertex: Optional[Vertex] = None
        self._vertices: list[Vertex] = []
        self._edges: list[HalfEdge] = []
        self._faces: list[Face] = []
        self._outer_face = Face(None)
        self._outer_face._is_outer = True
        self._faces.append(self._outer_face)

    def find_vertex(self, point: Point) -> Vertex:
        vertices = list(filter(lambda vertex: vertex.point == point, self._vertices))
        if len(vertices) > 1:
            raise AssertionError("More than one vertex at the given position")
        elif len(vertices) == 1:
            return vertices[0]
        else:
            return None
        
    def find_containing_face(self, point: Point):
        for face in self.inner_faces():
            face_cycle = face.outer_component.cycle
            #TODO: Need to triangulate and check each (convex) traingle
            pass
                

    @property
    def start_vertex(self) -> Optional[Vertex]:
        return self._start_vertex
    
    def vertices(self) -> Iterable[Vertex]:
        return self._vertices
    
    def edges(self) -> Iterable[HalfEdge]:
        return self._edges
    
    def faces(self) -> Iterable[Face]:
        return self._faces
    
    def inner_faces(self) -> Iterable[Face]:
        return list(filter(lambda face: not face.is_outer, self.faces()))
    
    def number_of_vertices(self) -> int:
        return len(self._vertices)

    def outer_face(self) -> Face:
        return self._outer_face
    
    def __len__(self) -> int:
        return self._number_of_vertices

