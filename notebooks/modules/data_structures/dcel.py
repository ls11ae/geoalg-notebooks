from __future__ import annotations
import copy
from itertools import chain
from typing import Iterable, Iterator, Optional, Tuple
import numpy as np

from ..geometry import LineSegment, Orientation as ORT, Point

from ..data_structures import Vertex, HalfEdge

class DoublyConnectedEdgeList:
    """ Simple DCEL without inner components """
    def __init__(self, points: Iterable[Point] = [], edges: Iterable[Tuple[int, int]] = []):
        self.clear()
        for point in points:
            self.add_vertex(point, edges)            

    def add_vertex(self, point: Point, edges: Iterable[Tuple[int, int]] = []) -> Vertex:
        if point in [vertex.point for vertex in self._vertices]:
            return None
        newVertex: Vertex = Vertex(point)
        self._vertices.append(newVertex)
        self._number_of_vertices += 1
        if len(self._vertices) > 0:
            self._start_vertex = self._vertices[0]

        for edge in edges:
            if (edge[0] > self._number_of_vertices or edge[0] <= 0
                or edge[1] > self._number_of_vertices or edge[1] <=0):
                continue
            if edge[0] != self._number_of_vertices and edge[1] != self._number_of_vertices:
                continue
            vertex_1 = self._vertices[edge[0]-1]
            vertex_2 = self._vertices[edge[1]-1]
            half_edge_1 = None
            half_edge_2 = None
            if vertex_1.edge == vertex_1.edge.twin: #single vertex
                half_edge_1 = vertex_1.edge
            else:
                half_edge_1 = HalfEdge(vertex_1)
            if vertex_2.edge == vertex_2.edge.twin: #single vertex
                half_edge_2 = vertex_2.edge
            else:
                half_edge_2 = HalfEdge(vertex_2)
                        
            #Find correct order around vertex_1
            search_edge = vertex_1.edge.twin
            if vertex_1.edge != vertex_1.edge.twin and vertex_1.edge.twin != vertex_1.edge.prev: # >1 adjacent vertices
                while not ((vertex_2.point.orientation(search_edge.origin.point, search_edge.destination.point) == ORT.LEFT
                        and (vertex_2.point.orientation(search_edge.next.origin.point, search_edge.next.destination.point) == ORT.LEFT
                        or search_edge.next.destination.point.orientation(search_edge.origin.point, search_edge.destination.point) == ORT.RIGHT))
                        or (vertex_2.point.orientation(search_edge.next.origin.point, search_edge.next.destination.point) == ORT.LEFT
                        and search_edge.origin.point.orientation(search_edge.next.origin.point, search_edge.next.destination.point) == ORT.RIGHT)):
                    search_edge = search_edge.next.twin
                    if search_edge == vertex_1.edge.twin:
                        raise Exception("Could not find a suitable edge")
            
            #Find correct order around vertex_2
            search_edge2 = vertex_2.edge.twin
            if vertex_2.edge != vertex_2.edge.twin and vertex_2.edge.twin != vertex_2.edge.prev: # >1 adjacent vertices
                while not ((vertex_2.point.orientation(search_edge2.origin.point, search_edge2.destination.point) == ORT.LEFT
                        and (vertex_2.point.orientation(search_edge2.next.origin.point, search_edge2.next.destination.point) == ORT.LEFT
                        or search_edge2.next.destination.point.orientation(search_edge2.origin.point, search_edge2.destination.point) == ORT.RIGHT))
                        or (vertex_2.point.orientation(search_edge2.next.origin.point, search_edge2.next.destination.point) == ORT.LEFT
                        and search_edge2.origin.point.orientation(search_edge2.next.origin.point, search_edge2.next.destination.point) == ORT.RIGHT)):
                    search_edge2 = search_edge2.next.twin
                    if search_edge2 == vertex_2.edge.twin:
                        raise Exception("Could not find a suitable edge")
                    
            half_edge_1._set_twin(half_edge_2)

            old_s1_next = search_edge.next
            old_s2_next = search_edge2.next

            search_edge._set_next(half_edge_1)
            search_edge2._set_next(half_edge_2)
            
            half_edge_1._set_next(old_s2_next)
            half_edge_2._set_next(old_s1_next)
            return newVertex

    def clear(self):
        self._start_vertex: Optional[Vertex] = None
        self._vertices: list[Vertex] = []
        #self._closing_edge: Optional[HalfEdge] = None
        #self._is_reversed: bool = False
        #self._has_diagonals: bool = False
        self._number_of_vertices: int = 0
    
    @property
    def start_vertex(self) -> Optional[Vertex]:
        return self._start_vertex
    
    def vertices(self) -> Iterator[Vertex]:
        return self._vertices
    
    def __len__(self) -> int:
        return self._number_of_vertices

