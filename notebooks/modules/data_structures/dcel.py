from __future__ import annotations
import copy
from itertools import chain
from typing import Iterable, Iterator, Optional, Tuple
import numpy as np

from ..geometry import LineSegment, Orientation as ORT, Point, EPSILON
from .objects import Vertex, HalfEdge, Face

class DoublyConnectedEdgeList:
    """ Simple DCEL without inner components """
    """ Edge order: Inner = ACW, Outer = CW """
    # TODO: Add additional methods (see ruler of the plane):
    # boundingbox, (init with boundingbox, init with linesegments and bounding box,)
    # addsegment, addline, # IMPROVE: addedge
    # PRIVATE: (addvertexinedgechain -> inside of add_edge), fixinnercomponents
    def __init__(self, points: Iterable[Point] = [], edges: Iterable[Tuple[int, int]] = []):
        self.clear()
        for point in points:
            self.add_vertex(point)
        for edge in edges:
            self.add_edge(edge)

        self._assert_well_formed()

    def add_vertex(self, point: Point) -> Vertex:
        # Check for correct insertion
        if point in [vertex.point for vertex in self._vertices]:
            return None
        on_edge = self._on_edge(point)
        if on_edge[0]:
            self.add_vertex_in_edge(on_edge[1], point)
        else:
            # Create vertex
            newVertex: Vertex = Vertex(point)
            self._vertices.append(newVertex)
            self._edges.append(newVertex.edge)
            newVertex.edge.incident_face = self.find_containing_face(point)

        # First Vertex inserted is the start vertex
        if len(self._vertices) > 0:
            self._start_vertex = self._vertices[0]
        return newVertex

    def add_edge(self, edge: Tuple[int, int]) -> None:
        if (edge[0] >= self.number_of_vertices or edge[0] < 0
            or edge[1] >= self.number_of_vertices or edge[1] < 0): # Impossible indicies
            return
        vertex_0 = self._vertices[edge[0]]
        vertex_1 = self._vertices[edge[1]]
        half_edge_0 = None
        half_edge_1 = None
        if vertex_0.edge == vertex_0.edge.twin: #single vertex
            half_edge_0 = vertex_0.edge
        else:
            half_edge_0 = HalfEdge(vertex_0)
            self._edges.append(half_edge_0)
        if vertex_1.edge == vertex_1.edge.twin: #single vertex
            half_edge_1 = vertex_1.edge
        else:
            half_edge_1 = HalfEdge(vertex_1)
            self._edges.append(half_edge_1)

        # Handle faces
        num_out_edges_0 = len(vertex_0.outgoing_edges())
        num_out_edges_1 = len(vertex_1.outgoing_edges())
        face_0, face_1 = None, None
        new_face = False
        if num_out_edges_0 != 0 and num_out_edges_1 != 0:
            face_0 = self.find_splitting_face(vertex_0, vertex_1.point)
            face_1 = self.find_splitting_face(vertex_1, vertex_0.point)

            # Check if new edge will create additional face TODO: Fill with logic once inner components are added
            new_inner_face = True # Inner component with both vertices on the cycle exists ("face inside the face")
            outer_component_split = True # Outer component (of the face) is split by the new edge
            new_face = new_inner_face or outer_component_split

        elif num_out_edges_0 != 0:
            face_0 = self.find_splitting_face(vertex_0, vertex_1.point)
            face_1 = self.find_containing_face(vertex_1.point)
        elif num_out_edges_1 != 0:
            face_0 = self.find_containing_face(vertex_0.point)
            face_1 = self.find_splitting_face(vertex_1, vertex_0.point)
        else:
            face_0 = self.find_containing_face(vertex_0)
            face_1 = self.find_containing_face(vertex_1)
            # TODO: When adding inner components: New inner component inside face: the new edge
        if face_0 != face_1:
            raise RuntimeError(f"Vertices {vertex_0} and {vertex_1} do not lie in the same face. Faces: {face_0} and {face_1}")

        half_edge_0.incident_face = face_0
        half_edge_1.incident_face = face_0 # face_0 == face_1

        # Find correct order around vertex_1
        search_edge = vertex_0.edge.twin
        if vertex_0.edge != vertex_0.edge.twin and vertex_0.edge.twin != vertex_0.edge.prev: # >1 adjacent vertices
            while not DoublyConnectedEdgeList._point_between_edge_and_next(vertex_1.point, search_edge):
                search_edge = search_edge.next.twin
                if search_edge == vertex_0.edge.twin:
                    raise Exception(f"Could not find a suitable edge while inserting {edge}")
        
        # Find correct order around vertex_2
        search_edge2 = vertex_1.edge.twin
        if vertex_1.edge != vertex_1.edge.twin and vertex_1.edge.twin != vertex_1.edge.prev: # >1 adjacent vertices
            while not DoublyConnectedEdgeList._point_between_edge_and_next(vertex_0.point, search_edge2):
                search_edge2 = search_edge2.next.twin
                if search_edge2 == vertex_1.edge.twin:
                    raise Exception(f"Could not find a suitable edge while inserting {edge}")
                
        # Set edge pointers
        half_edge_0._incident_face = face_0
        half_edge_1._incident_face = face_0

        half_edge_0._set_twin(half_edge_1)

        old_s1_next = search_edge.next
        old_s2_next = search_edge2.next

        search_edge._set_next(half_edge_0)
        search_edge2._set_next(half_edge_1)
        
        half_edge_0._set_next(old_s2_next)
        half_edge_1._set_next(old_s1_next)

        if new_face:
            face_1 = self._split_face(half_edge_0, face_0)
        else:
            face_1 = None

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
        
    def add_vertex_in_edge(self, edge: HalfEdge, point: Point) -> Vertex:
        # Checks for correct insertion
        if not edge in self.edges():
            raise Exception(f"Edge {edge} should already be part of the DCEL to add point {point} in it.")
        if not edge.origin.point != edge.destination.point and point.orientation(edge.origin.point, edge.destination.point) == ORT.BETWEEN:
            raise Exception(f"Point {point} should lie on the edge {edge}")
        if edge.origin.point == point or edge.destination.point == point: # vertex is one of the endpoints of the edge.
            return # vertex does not need to be added
        
        # Create vertex
        newVertex = Vertex(point)
        self._vertices.append(newVertex)
        self._edges.append(newVertex.edge)
        newHalfEdge = HalfEdge(newVertex)
        self._edges.append(newHalfEdge)

        old_next = edge.next
        old_twin_next = edge.twin.next

        # Fix twin and next pointers
        newVertex.edge._set_twin(edge.twin)
        newHalfEdge._set_twin(edge)

        edge._set_next(newVertex.edge)
        newVertex.edge._set_next(old_next)
        newVertex.edge.twin._set_next(newHalfEdge)
        newHalfEdge._set_next(old_twin_next)

        # Set faces
        newVertex.edge.incident_face = edge.incident_face
        newHalfEdge.incident_face = newVertex.edge.twin.incident_face

        return newVertex
        
    def find_containing_face(self, point: Point) -> Face:
        for face in self.inner_faces():
            if face.contains(point):
                return face
        return self.outer_face

    def find_splitting_face(self, vertex: Vertex, point: Point):
        out_edges = vertex.outgoing_edges()
        if len(out_edges) == 0:
            raise Exception("Vertex should be connected to face boundary")
        for edge in out_edges:
            if DoublyConnectedEdgeList._point_between_edge_and_next(point, edge.twin):
                return edge.twin.incident_face
        
    @staticmethod
    def _point_between_edge_and_next(point: Point, edge: HalfEdge) -> bool:
        edge_0, edge_1 = edge, edge.next
        edge_0_origin, edge_0_destination = edge_0.origin.point, edge_0.destination.point
        edge_1_origin, edge_1_destination = edge_1.origin.point, edge_1.destination.point
        # TODO: MAKE ROBUST
        # TODO: Maybe assert that point is not a vertex of the edges or on one of the edges.
        if edge_0.twin is edge_1:
            return True
        return point.orientation(edge_0_origin, edge_0_destination) == ORT.LEFT and (
            point.orientation(edge_1_origin, edge_1_destination) == ORT.LEFT or # Case A
            edge_1_destination.orientation(edge_0_origin, edge_0_destination) == ORT.RIGHT) or ( # Case B
            point.orientation(edge_1_origin, edge_1_destination) == ORT.LEFT and edge_0_origin.orientation(edge_1_origin, edge_1_destination) == ORT.RIGHT) # Case C

    @staticmethod
    def _on_cycle(edge: HalfEdge, vertex: Vertex) -> bool:
        return vertex in [cycle_edge.origin for cycle_edge in edge.cycle()]
    
    def _split_face(self, edge: HalfEdge, face: Face) -> Face:
        inner_edge = edge if not DoublyConnectedEdgeList._is_cycle_clockwise(edge) else edge.twin

        new_face = Face(inner_edge)
        self._faces.append(new_face)

        if not DoublyConnectedEdgeList._is_cycle_clockwise(inner_edge.twin):
            # Two new inner cycles formed from old one
            face.outer_component = inner_edge.twin
        
        DoublyConnectedEdgeList._update_face_in_cycle(inner_edge, new_face)
        
        #TODO: is this update (sometimes) necessary??
        # DoublyConnectedEdgeList._update_face_in_cycle(inner_edge.twin, face)

        return new_face

    @staticmethod
    def _update_face_in_cycle(start_edge: HalfEdge, face: Face):
        for edge in start_edge.cycle():
            edge.incident_face = face

    # Determines whether the cycle starting at a given edge is clockwise using the shoelace (trapezoid) formula
    @staticmethod
    def _is_cycle_clockwise(start_edge: HalfEdge, epsilon: float = EPSILON) -> bool:
        a = float(0)
        for edge in start_edge.cycle():
            a += (edge.origin.point.y + edge.destination.point.y) * (edge.origin.point.x - edge.destination.point.x)
        return a < -epsilon

    def _on_edge(self, point: Point) -> Tuple[bool, HalfEdge]:
        found_edges = list(filter(lambda edge: edge.origin.point != edge.destination.point and point.orientation(edge.origin.point, edge.destination.point) == ORT.BETWEEN, self.edges()))
        num_of_found_edges = len(found_edges)
        if num_of_found_edges < 0 or num_of_found_edges % 2 == 1:
            raise Exception(f"Point {point} lies on a non-possible amount of edges. Something is wrong in the structure of the DCEL.")
        elif num_of_found_edges == 0:
            return (False, None)
        else: # num_of_found_edges is even and >=2, if greater than 2 than it is on a vertex.
            return (True, found_edges[0])

    def _assert_well_formed(self, epsilon = EPSILON):
        # Check empty DCEL
        if self.number_of_vertices == 0:
            if len(self.vertices()) != 0 or len(self.edges()) != 0 or len(self.faces()) != 0:
                raise Exception(f"Malformed DCEL: Should be empty.")
            return

        for edge in self.edges():
            # Check previous and next connections
            if edge.prev.next != edge:
                raise Exception(f"Malformed DCEL: prev-next connection error in edge {edge}")
            if edge.next.prev != edge:
                raise Exception(f"Malformed DCEL: next-prev connection error in edge {edge}")
    
            # Check point position of adjacent edges
            if edge.prev.destination.point != edge.origin.point:
                raise Exception(f"Malformed DCEL: prev.destination-origin error in edge {edge}")
            if edge.next.origin.point != edge.destination.point:
                raise Exception(f"Malformed DCEL: next.origin-destination error in edge {edge}")
            
            # Check zero-length edges
            if edge.length <= epsilon:
                raise Exception(f"Malformed DCEL: edge of length zero: {edge}")

            # Check twin references
            if edge.twin.twin != edge:
                raise Exception(f"Malformed DCEL: invalid twin refernce in edge {edge}")
            if edge.origin.point != edge.twin.destination.point or edge.destination.point != edge.twin.origin.point:
                raise Exception(f"Malformed DCEL: Invalid twin point positions")

            # Check edge faces
            if not edge.incident_face.is_outer and edge not in edge.incident_face.outer_half_edges(): #TODO add inner half edges
                raise Exception(f"Malformed DCEL: edge ({edge}) face mismatch with face components")
            
        for face in self.faces():
            # Check is outer face
            if face.is_outer and face.outer_component != None:
                raise Exception(f"Malformed DCEL: outer face has an outer component")

            # Check for single outer face
            if face.is_outer and face != self.outer_face:
                raise Exception(f"Malformed DCEL: More than one outer face: {face}")
            
            # Check cycle around outer component of face
            for edge in face.outer_half_edges():
                if edge.incident_face != face:
                    raise Exception(f"Malformed DCEL: Unexpected incident face of edge {edge}")
                
            # Check cycle around inner components
            # TODO: add inner component check

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
    
    @property
    def number_of_vertices(self) -> int:
        return len(self._vertices)

    @property
    def outer_face(self) -> Face:
        return self._outer_face
    
    def __len__(self) -> int:
        return self._number_of_vertices
