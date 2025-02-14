from __future__ import annotations
from ...geometry.animation_base import AnimationObject, AnimationEvent, AppendEvent, PopEvent
from ...data_structures import DoublyConnectedEdgeList, Vertex, HalfEdge, Face
from ...geometry import Rectangle, Point, PointList
from typing import Iterator

class DCELAnimator(AnimationObject):
    def __init__(self, boundingBox : Rectangle):
        super().__init__()
        self._dcel : DoublyConnectedEdgeList = DoublyConnectedEdgeList()
        self._points : list[Point] = []
        self._animation_events = []
        self._illformed : bool = False
        self._init_bounding_box(boundingBox)
    
    def _init_bounding_box(self, boundingBox: Rectangle):
        #if the bounding box is illformed, all further calculations don't make sense
        if((boundingBox.left == boundingBox.right) or (boundingBox.lower == boundingBox.upper)):
            self._illformed = True
            return

        lowLeft = Point(boundingBox.left, boundingBox.lower)
        upLeft = Point(boundingBox.left, boundingBox.upper)
        upRight = Point(boundingBox.right, boundingBox.upper)
        lowRight = Point(boundingBox.right, boundingBox.lower)
        #add bottom left first so it can be accessed easily later
        self.add_vertex(lowLeft)
        self.add_vertex(upLeft)
        self.add_vertex(upRight)
        self.add_vertex(lowRight)
        self.add_edge(lowLeft, upLeft)
        self.add_edge(upLeft, upRight)
        self.add_edge(upRight, lowRight)
        self.add_edge(lowRight, lowLeft)

    def add_vertex(self, point : Point) -> Vertex:
        v = self._dcel.add_vertex(point)
        self._animation_events.append(VertexAddedEvent(point))
        return v

    def add_edge(self, p1 : Point, p2 : Point):
        self._dcel.add_edge_by_points(p1, p2)
        self._animation_events.append(EdgeAddedEvent(p1, p2))

    def add_point(self, point : Point):
        self._animation_events.append(AppendEvent(point))
        self._points.append(point)

    def add_vertex_on_edge(self, point : Point, edge : HalfEdge) -> Vertex:
        origin = PointList(edge.origin.x, edge.origin.y, [])
        dest = PointList(edge.destination.x, edge.destination.y, [])
        p = PointList(point.x, point.y, [])
        self._animation_events.append(EdgeRemovedEvent(origin, dest))
        self._animation_events.append(VertexAddedEvent(point))
        self._animation_events.append(EdgeAddedEvent(origin, point))
        self._animation_events.append(EdgeAddedEvent(point, dest))
        v = self._dcel.add_vertex_in_edge(edge, point)
        return v
    
    def animate_edge(self, p1 : Point, p2 : Point):
        self._animation_events.append(AppendEvent(p1))
        self._animation_events.append(AppendEvent(p2))
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())

    def points(self) -> Iterator[Point]:
        points : list[Point] = []
        one = True
        for v in self._dcel.vertices:
            p = PointList(v.point.x, v.point.y, [])
            points.append(p)
            if v.edge.destination is not v:
                e = v.edge
                p.data.append(Point(e.destination.point.x, e.destination.point.y))
                e = e.twin.next
                while(e != v.edge):
                    p.data.append(Point(e.destination.point.x, e.destination.point.y))
                    e = e.twin.next
        points = points + self._points
        return iter(points)
    
    def get_next_face(self, v : Vertex, p : Point) -> Face:
        return self._dcel.find_splitting_face(v,p)
    
    def get_bounding_box(self) -> list[HalfEdge]:
        return self._dcel.outer_face.inner_half_edges()
    
    def get_outer_face(self) -> Face:
        return self._dcel.outer_face
    
    def get_bottom_left(self) -> Vertex:
        return self._dcel.start_vertex
    
    def get_splitting_face(self, v : Vertex, p : Point) -> Face:
        return self._dcel.find_splitting_face(v,p)

    def vertices(self) -> list[Vertex]:
        return self._dcel.vertices

    @property
    def illformed(self):
        return self._illformed

class VertexAddedEvent(AnimationEvent):
    def __init__(self, p : Point):
        self._p = PointList(p.x,p.y, [])

    def execute_on(self, points: list[Point]):
        points.append(self._p)

class EdgeAddedEvent(AnimationEvent):
    def __init__(self, p1: Point, p2 : Point):
        self._p1 = PointList(p1.x,p1.y, [])
        self._p2 = PointList(p2.x,p2.y, [])

    def execute_on(self, points : list[Point]):
        for p in points:
            if isinstance(p, PointList):
                if p == self._p1:
                    p.data.append(self._p2)
                if p == self._p2:
                    p.data.append(self._p1)

class EdgeRemovedEvent(AnimationEvent):
    def __init__(self, p1: PointList, p2 : PointList):
        self._p1 = p1
        self._p2 = p2

    def execute_on(self, points : list[Point]):
        for p in points:
            if not isinstance(p, PointList):
                continue
            if p is self._p1 and p.data.__contains__(self._p2):
                p.data.remove(self._p2)
            if p is self._p2 and p.data.__contains__(self._p1):
                p.data.remove(self._p1)
