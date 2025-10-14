from __future__ import annotations
from typing import Iterable, Optional, Tuple
import numpy as np

from ..geometry import LineSegment, Orientation as ORT, Point, EPSILON
from .objects import Vertex, HalfEdge, Face

class DoublyConnectedEdgeList:
    """ 
    Simple DCEL without inner components 
    Edge order: Inner = ACW, Outer = CW
    """
    # TODO: constructors for bounding-box (init with boundingbox, init with linesegments and bounding box) (see ruler of the plane):
    # methods: addsegment, addline
    def __init__(self, points: Iterable[Point], edges: Iterable[Tuple[int, int]]):
        self.clear()
        for point in points:
            self.add_vertex(point)
        for edge in edges:
            self.add_edge(edge)
        self._assert_well_formed()

    def add_vertex(self, point: Point) -> Vertex:
        """ Add a new vertex to the DCEL """
        # Check for correct insertion
        for vertex in self._vertices:
            if point is vertex.point:
                return vertex

        on_edge, edge = self._on_edge(point)
        if on_edge:
            new_vertex = self.add_vertex_in_edge(edge, point)
        else:
            # Create vertex
            new_vertex: Vertex = Vertex(point)
            self._vertices.append(new_vertex)
            self._edges.append(new_vertex.edge)
            new_vertex.edge.incident_face = self.find_containing_face(point)

        # First Vertex inserted is the start vertex
        if len(self._vertices) > 0:
            self._start_vertex = self._vertices[0]
        # And new vertex is always the last vertex
        self._last_added_vertex = new_vertex
        return new_vertex

    def add_edge(self, edge: Tuple[int, int], check_edge: bool = False) -> bool:
        """Adds a new edge to the DCEL. 
        
        The edge is given by the indicies of the vertices.
        As a default, it is assumed, that the given edge can be inserted and does not cross other edges or vertices.
        In that case it is always returned True.
        If the potential edge is checked it is returned whether the edge could be added.
        """
        if (edge[0] >= self.number_of_vertices or edge[0] < 0
            or edge[1] >= self.number_of_vertices or edge[1] < 0): # Impossible indicies
            return False
        if check_edge and not self._possible_edge(self._vertices[edge[0]], self._vertices[edge[1]]):
            return False
        self._add_edge(self._vertices[edge[0]], self._vertices[edge[1]])
        return True

    def add_edge_by_points(self, point: Point, other_point: Point):
        """Adds a new edge to the DCEL. 
        
        The edge is given by two points.
        If either of the points is not in the DCEL an exception is raised.
        If the edge is already in the DCEL nothing happens.
        """
        vertex_0, vertex_1 = None, None
        for vertex in self.vertices:
            if vertex.point == point:
                vertex_0 = vertex
            if vertex.point == other_point:
                vertex_1 = vertex
            if vertex_0 is not None and vertex_1 is not None:
                break
        for edge in self.edges:
            if edge.origin.point == point and edge.destination.point == other_point:
                return
        if vertex_0 is None or vertex_1 is None:
            raise ValueError(f"Both points {point} and {other_point} need to be part of the DCEL to insert as an edge")
        self._add_edge(vertex_0, vertex_1)


    def _add_edge(self, vertex_0: Vertex, vertex_1: Vertex):
        half_edge_0 = None
        half_edge_1 = None
        if vertex_0.edge == vertex_0.edge.twin:  # vertex 0 has no outgoing connections
            half_edge_0 = vertex_0.edge
        else:
            half_edge_0 = HalfEdge(vertex_0)
            self._edges.append(half_edge_0)
        if vertex_1.edge == vertex_1.edge.twin:  # vertex_1 has no edges
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

            # Check if new edge will create additional face
            # An Inner component with both vertices on the cycle exists
            new_inner_face = len(list(filter(lambda e: e.vertex_on_cycle(vertex_0) and e.vertex_on_cycle(vertex_1), face_0.inner_components))) >= 1
            # OR outer component (of the face) is split by the new edge
            outer_component_split = (not face_0.is_outer) and face_0.outer_component.vertex_on_cycle(vertex_0) and face_0.outer_component.vertex_on_cycle(vertex_1)
            new_face = new_inner_face or outer_component_split

        elif num_out_edges_0 != 0:
            face_0 = self.find_splitting_face(vertex_0, vertex_1.point)
            face_1 = self.find_containing_face(vertex_1.point)
        elif num_out_edges_1 != 0:
            face_0 = self.find_containing_face(vertex_0.point)
            face_1 = self.find_splitting_face(vertex_1, vertex_0.point)
        else:
            face_0 = self.find_containing_face(vertex_0.point)
            face_1 = self.find_containing_face(vertex_1.point)
            
            # new inner component
            face_0.inner_components.append(half_edge_0)
        if face_0 != face_1:
            raise RuntimeError(f"Vertices {vertex_0} and {vertex_1} do not lie in the same face. Faces: {face_0} and {face_1}")

        half_edge_0.incident_face = face_0
        half_edge_1.incident_face = face_0  # face_0 == face_1

        # Find correct order around vertex_0
        search_edge = vertex_0.edge.twin
        if vertex_0.edge != vertex_0.edge.twin and vertex_0.edge.twin != vertex_0.edge.prev: # >1 adjacent vertices
            while not DoublyConnectedEdgeList.point_between_edge_and_next(vertex_1.point, search_edge):
                search_edge = search_edge.next.twin
                if search_edge == vertex_0.edge.twin:
                    raise Exception(f"Could not find a suitable edge while inserting edge between vertices {vertex_0} and {vertex_1}")
        
        # Find correct order around vertex_1
        search_edge2 = vertex_1.edge.twin
        if vertex_1.edge != vertex_1.edge.twin and vertex_1.edge.twin != vertex_1.edge.prev: # >1 adjacent vertices
            while not DoublyConnectedEdgeList.point_between_edge_and_next(vertex_0.point, search_edge2):
                search_edge2 = search_edge2.next.twin
                if search_edge2 == vertex_1.edge.twin:
                    raise Exception(f"Could not find a suitable edge while inserting edge between vertices {vertex_0} and {vertex_1}")
                
        # Set edge pointers
        half_edge_0._incident_face = face_0  # TODO: Remove?
        half_edge_1._incident_face = face_0

        half_edge_0.twin = half_edge_1

        old_s1_next = search_edge.next
        old_s2_next = search_edge2.next

        search_edge.next = half_edge_0
        search_edge2.next = half_edge_1
        
        half_edge_0.next = old_s2_next
        half_edge_1.next = old_s1_next

        if new_face:
            face_1 = self._split_face(half_edge_0, face_0)
        else:
            face_1 = None

        # fix inner components: inner components has become part of outer components
        # or inner components have merged
        self._fix_inner_components(half_edge_0, half_edge_1, face_0, face_1)

    def clear(self):
        """ Clears the DCEL """
        self._start_vertex: Optional[Vertex] = None
        self._last_added_vertex: Optional[Vertex] = None
        self._vertices: list[Vertex] = []
        self._edges: list[HalfEdge] = []
        self._faces: list[Face] = []
        self._outer_face = Face(None)
        self._outer_face._is_outer = True
        self._faces.append(self._outer_face)

    def find_vertex(self, point: Point) -> Vertex | None:
        """ Gives a vertex for a point if it is in the DCEL, None otherwise. """
        vertices = list(filter(lambda vertex: vertex.point == point, self._vertices))
        if len(vertices) > 1:
            raise AssertionError("More than one vertex at the given position")
        elif len(vertices) == 1:
            return vertices[0]
        else:
            return None
        
    def add_vertex_in_edge(self, edge: HalfEdge, point: Point) -> Vertex | None:
        """ Adds a vertex on an existing edge by splitting it. """
        # Checks for correct insertion
        if not edge in self.edges:
            raise Exception(f"Edge {edge} should already be part of the DCEL to add point {point} on it.")
        if not edge.origin.point != edge.destination.point and point.orientation(edge.origin.point, edge.destination.point) == ORT.BETWEEN:
            raise Exception(f"Point {point} should lie on the edge {edge}")
        if edge.origin.point == point or edge.destination.point == point:
            return None #vertex is one of the endpoints of the edge
        
        # Create vertex
        new_vertex = Vertex(point)
        self._vertices.append(new_vertex)
        self._edges.append(new_vertex.edge)
        new_half_edge = HalfEdge(new_vertex)
        self._edges.append(new_half_edge)

        old_next = edge.next
        old_twin_next = edge.twin.next

        # Fix twin and next pointers
        new_vertex.edge.twin = edge.twin
        new_half_edge.twin = edge

        edge.next = new_vertex.edge
        new_vertex.edge.next  = old_next
        new_vertex.edge.twin.next = new_half_edge
        new_half_edge.next = old_twin_next

        # Set faces
        new_vertex.edge.incident_face = edge.incident_face
        new_half_edge.incident_face = new_vertex.edge.twin.incident_face

        return new_vertex
        
    def _possible_edge(self, vertex: Vertex, other_vertex: Vertex) -> bool:
        # Vertices are not part to the same face
        num_out_edges_0 = len(vertex.outgoing_edges())
        num_out_edges_1 = len(other_vertex.outgoing_edges())
        if num_out_edges_0 != 0 and num_out_edges_1 != 0:
            face_0 = self.find_splitting_face(vertex, other_vertex.point)
            face_1 = self.find_splitting_face(other_vertex, vertex.point)
        elif num_out_edges_0 != 0:
            face_0 = self.find_splitting_face(vertex, other_vertex.point)
            face_1 = self.find_containing_face(other_vertex.point)
        elif num_out_edges_1 != 0:
            face_0 = self.find_containing_face(vertex.point)
            face_1 = self.find_splitting_face(other_vertex, vertex.point)
        else:
            face_0 = self.find_containing_face(vertex.point)
            face_1 = self.find_containing_face(other_vertex.point)            
        if face_0 != face_1:
            return False

        # Another edge crosses the potential edge
        potential_edge = LineSegment(vertex.point, other_vertex.point)
        if face_0.outer_component is not None:
            for cycle_edge in face_0.outer_component.cycle():
                intersection = potential_edge.intersection(LineSegment(cycle_edge.origin.point, cycle_edge.destination.point))
                if intersection is not None and intersection != vertex.point and intersection != other_vertex.point:
                    return False
        for inner_component in face_0.inner_components:
            for cycle_edge in inner_component.cycle():
                if potential_edge.intersection(LineSegment(cycle_edge.origin.point, cycle_edge.destination.point)) is not None:
                    return False
        return True
    
    def find_containing_face(self, point: Point) -> Face:
        """ Returns the faces which contains the given point. """
        for face in self.inner_faces():
            if face.contains(point):
                return face
        return self.outer_face

    def find_splitting_face(self, vertex: Vertex, point: Point) -> Face:
        """ Return the face that is split by a line segment between the given vertex and point and is closest to the vertex. """
        out_edges = vertex.outgoing_edges()
        if len(out_edges) == 0:
            raise Exception(f"Vertex {vertex} should be connected to face boundary")
        for edge in out_edges:
            if DoublyConnectedEdgeList.point_between_edge_and_next(point, edge.twin):
                return edge.twin.incident_face
        raise Exception(f"Malformed DCEL: point {point} must split a face around vertex {vertex}")
    
    def find_edges_of_vertex(self, vertex: Vertex) -> list[HalfEdge]:
        return [edge for edge in self.edges if edge.origin == vertex]
        
    @staticmethod
    def point_between_edge_and_next(point: Point, edge: HalfEdge) -> bool:
        edge_0, edge_1 = edge, edge.next
        edge_0_origin, edge_0_destination = edge_0.origin.point, edge_0.destination.point
        edge_1_origin, edge_1_destination = edge_1.origin.point, edge_1.destination.point
        
        if edge_0.twin is edge_1:
            return True
        #point is left of both edges
        case_a1 = point.orientation(edge_0_origin, edge_0_destination) == ORT.LEFT and point.orientation(edge_1_origin, edge_1_destination) == ORT.LEFT# Case A
        #point is left of the first edge and edges make a right turn
        case_a2 = point.orientation(edge_0_origin, edge_0_destination) == ORT.LEFT and edge_1_destination.orientation(edge_0_origin, edge_0_destination) == ORT.RIGHT
        #point is left of second edge and edges make a right turn
        case_b = (point.orientation(edge_1_origin, edge_1_destination) == ORT.LEFT and edge_0_origin.orientation(edge_1_origin, edge_1_destination) == ORT.RIGHT)
        return case_a1 or case_a2 or case_b # Case C (where?)

    def _split_face(self, edge: HalfEdge, face: Face) -> Face:
        inner_edge = edge if not edge.is_cycle_clockwise() else edge.twin

        new_face = Face(inner_edge)
        self._faces.append(new_face)

        if not inner_edge.twin.is_cycle_clockwise():
            # Two new inner cycles formed from old one
            face.outer_component = inner_edge.twin
        
        inner_edge.update_face_in_cycle(new_face)
        
        #TODO: is this update (sometimes) necessary??
        # inner_edge.twin.update_face_in_cycle(face)

        return new_face
    
    def _fix_inner_components(self, edge_0: HalfEdge, edge_1: HalfEdge, old_face: Face, new_face: Face):
        # remove all inner components that were affected by adding halfedges
        old_face.inner_components = filter(
            lambda e: e.incident_face == old_face and edge_0 not in e.cycle() and edge_1 not in e.cycle(), 
            old_face.inner_components)

        # add one of the half edges if both not part of the outer component
        if old_face.is_outer or not (edge_0 in old_face.outer_component.cycle() or edge_1 in old_face.outer_component.cycle()):
            old_face.inner_components.append(edge_0 if edge_0.incident_face == old_face else edge_1)

        # redistribute inner components that are now contained inside the new face
        if new_face is not None:
            components_to_move = list(filter(
                lambda e: new_face.contains(e.origin.point) and not (edge_0 in e.cycle() or edge_1 in e.cycle()),
                old_face.inner_components))
            for component in components_to_move:
                #TODO: is it necessary to check intersection of component with edge_0? (see ruler of the plane)

                # move components to new face
                old_face.inner_components.remove(component)
                new_face.inner_components.append(component)

                component.update_face_in_cycle(new_face)


    def _on_edge(self, point: Point):
        found_edges = list(filter(lambda edge: edge.origin.point != edge.destination.point and point.orientation(edge.origin.point, edge.destination.point) == ORT.BETWEEN, self.edges))
        num_of_found_edges = len(found_edges)
        if num_of_found_edges < 0 or num_of_found_edges % 2 == 1:
            raise Exception(f"Point {point} lies on a non-possible amount of edges. Something is wrong in the structure of the DCEL.")
        elif num_of_found_edges == 0:
            return False, None
        else: # num_of_found_edges is even and >=2, if greater than 2 than it is on a vertex.
            return True, found_edges[0]

    def _assert_well_formed(self, epsilon = EPSILON):
        # Check empty DCEL
        if self.number_of_vertices == 0:
            if len(self.vertices) != 0 or len(self.edges) != 0 or len(self.faces) != 1:
                raise Exception(f"Malformed DCEL: Should be empty.")
            return

        for edge in self.edges:
            # Skip edges of single vertices
            if edge == edge.twin:
                continue

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
            if edge not in edge.incident_face.outer_half_edges() \
                and edge not in edge.incident_face.inner_half_edges():
                raise Exception(f"Malformed DCEL: edge ({edge}) face mismatch with face components")
            
        for face in self.faces:
            # Check is outer face
            if face.is_outer and face.outer_component is not None:
                raise Exception(f"Malformed DCEL: outer face has an outer component")

            # Check for single outer face
            if face.is_outer and face != self.outer_face:
                raise Exception(f"Malformed DCEL: More than one outer face: {face}")
            
            # Check cycle around outer component of face
            for edge in face.outer_half_edges():
                if edge.incident_face != face:
                    raise Exception(f"Malformed DCEL: Unexpected incident face of edge {edge}")
                
            # Check cycle around inner components
            for edge in face.inner_components:
                if edge.incident_face != face:
                    raise Exception(f"Malformed DCEL: Unexpected incident face ({edge.incident_face}) \
                                    of edge {edge} which is inner component of face {face}")

    @property
    def start_vertex(self) -> Optional[Vertex]:
        return self._start_vertex
    
    @property
    def vertices(self) -> list[Vertex]:
        return self._vertices
    
    @property
    def points(self) -> list[Point]:
        return [vertex.point for vertex in self._vertices]

    @property
    def edges(self) -> list[HalfEdge]:
        return self._edges
    
    @property
    def faces(self) -> list[Face]:
        return self._faces
    
    def inner_faces(self) -> list[Face]:
        return list(filter(lambda face: not face.is_outer, self.faces))
    
    @property
    def number_of_vertices(self) -> int:
        return len(self._vertices)

    @property
    def outer_face(self) -> Face:
        return self._outer_face