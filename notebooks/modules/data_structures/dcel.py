from __future__ import annotations
import copy
from itertools import chain
from typing import Iterable, Iterator, Optional, Tuple
import numpy as np

from ..geometry import LineSegment, Orientation as ORT, Point
from .objects import Vertex, HalfEdge, Face
# from .dcsp import DoublyConnectedSimplePolygon
# from .triangulation import monotone_triangulation

class DoublyConnectedEdgeList:
    """ Simple DCEL without inner components """
    # TODO: Add additional methods (see ruler of the plane):
    # boundingbox, (init with boundingbox, init with linesegments and bounding box,)
    # addvertexinedge, addsegment, addline, 
    # IMPROVE: AddEdge, splitface, getsplittingface, getcontainingface, (addface,)
    # PRIVATE: oncycle, addvertexinedgechain, fixinnercomponents, iscycleclockwise, updatefaceincycle, onedge, assertwellformed
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
        
    def find_containing_face(self, point: Point) -> Face:
        for face in self.inner_faces():
            if face.contains(point):
                return face
        return self.outer_face

    def find_splitting_face(self, vertex: Vertex, point: Point):
        out_edges = vertex.outgoing_edges()
        if out_edges == 0:
            raise Exception("Vertex should be connected to face boundary")
        for edge in out_edges:
            if point.orientation(edge.origin, edge.destination) == ORT.LEFT \
                and point.orientation(edge.prev.origin, edge.prev.destination) == ORT.LEFT:
                return edge.incident_face
                #  TODO: Double-check, maybe use edge-insertion-comparision
        

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

