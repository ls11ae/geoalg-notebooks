from __future__ import annotations
from base import AnimationObject, AnimationEvent, AppendEvent
from ..data_structures import DoublyConnectedEdgeList, Vertex, HalfEdge
from ..geometry import Rectangle, Point, PointList

class DCELAnimator(AnimationObject):
    def __init__(self, boundingBox : Rectangle):
        self._dcel : DoublyConnectedEdgeList = DoublyConnectedEdgeList()
        self._init_bounding_box(boundingBox)
        super.__init__()
    
    def _init_bounding_box(self, boundingBox: Rectangle):
        upLeft = Point(boundingBox.left, boundingBox.upper)
        lowLeft = Point(boundingBox.left, boundingBox.lower)
        upRight = Point(boundingBox.left, boundingBox.lower)
        lowRight = Point(boundingBox.right, boundingBox.lower)

        self.add_vertex(upLeft)
        self.add_vertex(lowLeft)
        self.add_vertex(upRight)
        self.add_vertex(lowRight)

        self._dcel.add_edge(lowLeft, upLeft)
        self._dcel.add_edge(upLeft, upRight)
        self._dcel.add_edge(upRight, lowRight)
        self._dcel.add_edge(lowRight, lowLeft)

    def add_vertex(self, point : PointList):
        self._dcel.add_vertex(point)
        self._animation_events.append(AppendEvent(PointList))

    def add_edge(self, point1 : PointList, point2 : PointList):
        self._dcel.add_edge(point1, point2)
        self._animation_events.append(EdgeAddedEvent(point1, point2))

    def add_vertex_on_edge(self, point : Point, edge : HalfEdge):
        self._animation_events.append(EdgeRemovedEvent(edge.origin.point, edge.twin.origin.point))
        v = self._dcel.add_vertex_in_edge(point, edge)
        self._animation_events.append(AppendEvent(point))

        self._animation_events.append(EdgeRemovedEvent(edge.origin.point, edge.twin.origin.point))
        self._animation_events.append(EdgeRemovedEvent(edge.next.origin.point, edge.next.twin.origin.point))


class EdgeAddedEvent(AnimationEvent):
    def __init__(self, p1: PointList, p2 : PointList):
        self._p1 = p1
        self._p2 = p2

    def execute_on(self, data : list[Point]):
        for p in data:
            if not isinstance(p, PointList):
                continue
            if p is self._p1:
                p.data().append(self._p2)
            if p is self._p2:
                p.data().append(self._p1)

class EdgeRemovedEvent():
    def __init__(self, p1: PointList, p2 : PointList):
        self._p1 = p1
        self._p2 = p2

    def execute_on(self, data : list[Point]):
        for p in data:
            if not isinstance(p, PointList):
                continue
            if p is self._p1 and p.data().__contains__(self._p2):
                p.data().remove(self._p2)
            if p is self._p2 and p.data().__contains__(self._p1):
                p.data().remove(self._p1)

