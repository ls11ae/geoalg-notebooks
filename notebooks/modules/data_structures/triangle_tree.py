from __future__ import annotations
from .objects import HalfEdge, Vertex
from ..geometry import Point
from .dcel import DoublyConnectedEdgeList as DCEL
from numpy import linalg

P0 = Point(-3000, 3000)
P1 = Point(3000, 3000)
P2 = Point(200, -3000)

class Triangulation(DCEL):

    def __init__(self, p0 : Point = P0, p1 : Point = P1, p2 : Point = P2):
        super().__init__([p0,p1,p2], [[0,1], [1,2], [2,0]])

    def insert_point(self, p : Point) -> Vertex | None:
        # this can be done more efficient TODO
        f = self.find_containing_face(p)
        if f is self.outer_face:
            # point is outside the large dummy triangle
            return None
        if list(self.points).__contains__(p):
            # point is already in the dcel
            return None
        v = self.add_vertex(p)
        if len(v.outgoing_edges()) == 2:
            #point was added on an edge
            for e in v.outgoing_edges():
                self.add_edge_by_points(p, e.next.destination)
        elif len(v.outgoing_edges()) == 0:
            #point was added in a face
            for f_p in f.outer_points():
                self.add_edge_by_points(p, f_p)
        else:
            raise ValueError("new Vertex is neither on an Edge or in a Face (No idea how you did that, congrats)")
        return v

    def is_legal(self, e : HalfEdge) -> bool:
        #edges adjacent to the outer face cannot be illegal as there is no fourth vertex
        if e.incident_face is self._outer_face or e.twin.incident_face is self._outer_face:
            return True
        opposite_vertex = e.twin.next.destination
        
        center = self.center_of_circumcircle(e)
        return center.distance(e.origin.point) < center.distance(opposite_vertex.point)
    
    @staticmethod
    def center_of_circumcircle(e : HalfEdge) -> Point:
        p0 = e.origin.point
        p1 = e.destination.point
        p2 = e.next.destination.point
        a = linalg.det([[p0.x, p0.y, 1],[p1.x, p1.y, 1],[p2.x, p2.y, 1]])
        b_x = -linalg.det([[pow(p0.x,2) + pow(p0.y,2), p0.y, 1],
                          [pow(p1.x,2) + pow(p1.y,2), p1.y, 1],
                          [pow(p2.x,2) + pow(p2.y,2), p2.y, 1]])
        b_y = linalg.det([[pow(p0.x,2) + pow(p0.y,2), p0.x, 1],
                          [pow(p1.x,2) + pow(p1.y,2), p1.x, 1],
                          [pow(p2.x,2) + pow(p2.y,2), p2.x, 1]])
        return Point(-b_x/(2*a), -b_y/(2*a))
    
    def flip_edge(self, e : HalfEdge) -> bool:
        #edges on the outer face cannot be flipped as there is not fourth vertex
        if e.incident_face is self.outer_face or e.twin.incident_face is self.outer_face:
            return False
        if not self._edges.__contains__(e):
            return False
        #save pointers to makes rerouting at least somewhat readable
        t = e.twin
        e_next = e.next
        e_prev = e.prev
        t_next = t.next
        t_prev = t.prev
        #update connections of the flipped edge
        e.prev = e_next
        e.next = t_prev
        t.prev = t_next
        t.next = e_prev
        #update vertices of flipped edge
        e.origin = e.prev.destination
        t.origin = t.prev.destination
        #update connections between e.prev and e.next
        e.prev.prev = e.next
        t.prev.prev = t.next
        #update vertices
        e.origin.edge = e
        t.origin.edge = t
        e.prev.origin.edge = e.prev
        t.prev.origin.edge = t.prev
        #update faces
        e.next.incident_face = e.incident_face
        e.next.next.incident_face = e.incident_face
        t.next.incident_face = t.incident_face
        t.next.next.incident_face = t.incident_face
        e.incident_face.outer_component = e
        t.incident_face.outer_component = t
        return True

    def _remove_edge(self, e : HalfEdge) -> bool:
        if not self._edges.__contains__(e):
            return False
        self._edges.remove(e)
        return True
        
    def edges_as_points(self) -> list[Point]:
        #since the edge drawn dont have a direction this will draw every edge twice
        points = []
        for e in self.edges:
            #if not e.origin.point in [P0,P1,P2] and not e.destination.point in [P0, P1, P2]:
            points.append(e.origin.point)
            points.append(e.destination.point)
        return points

    def reset(self, p0 : Point = P0, p1 : Point = P1, p2 : Point = P2):
        super().clear()
        super().__init__([p0,p1,p2], [[0,1], [1,2], [2,0]])