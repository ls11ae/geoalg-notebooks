from __future__ import annotations
from ..triangle_tree import Triangulation
from ...geometry import AnimationObject, AnimationEvent, Point, PointFloat, AppendEvent, PopEvent, PointPair
from typing import Iterator, Iterable

from ..objects import HalfEdge, Vertex

class EdgeAnimator(AnimationObject):
    def __init__(self):
        super().__init__()
        self._illegal_edges : list[HalfEdge] = []
        self._checked_edges : list[HalfEdge] = []

    def animate_circumcircle(self, e : HalfEdge):
        center = Triangulation.center_of_circumcircle(e)
        self._animation_events.append(AppendEvent(PointFloat(center.x, center.y, center.distance(e.origin.point))))
        self._animation_events.append(AppendEvent(Point(e.twin.next.destination.point.x, e.twin.next.destination.point.y)))
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())

    def highlight_edge(self, e : HalfEdge):
        self._animation_events.append(AppendEvent(PointPair(e.origin.point.x, e.origin.point.y, e.destination.point)))

    def unhighlight_edge(self):
        self._animation_events.append(PopEvent())

    def add_illegal_edge(self, e : HalfEdge):
        self._illegal_edges.append(e)

    def edge_or_twin_checked(self, e : HalfEdge) -> bool:
        return self._checked_edges.__contains__(e) or self._checked_edges.__contains__(e.twin)

    def add_checked_edge(self, e : HalfEdge):
        self._checked_edges.append(e)
        self._checked_edges.append(e.twin)

    def points(self) -> Iterator[Point]:
        points = []
        for e in self._illegal_edges:
            points.append(e.origin.point)
            points.append(e.destination.point)
        return iter(points)

class Incremental_Construction_Animator(AnimationObject):
    def __init__(self):
        super().__init__()
        self._triangulation = Triangulation()

    def points(self) -> Iterator[Point]:
        return self._triangulation.edges_as_points()
    
    def insert_point(self, p : Point):
        v =  self._triangulation.insert_point(p)
        if v is None:
            return None
        else:
            for e in v.outgoing_edges():
                self._animation_events.append(AppendEvent(p))
                self._animation_events.append(AppendEvent(PointPair(p.x, p.y, e.destination.point)))
            return v

    def legalize_edge(self, e : HalfEdge, v : Vertex):
        if not self.is_legal(e):
            if e.next.destination is v:
                e = e.twin
            next = e.next
            prev = e.prev
            self.flip_edge(e)
            self.legalize_edge(next, v)
            self.legalize_edge(prev, v)

    def is_legal(self, e : HalfEdge) -> bool:
        return self._triangulation.is_legal(e)
    
    def flip_edge(self, e : HalfEdge):
        new_p0, new_p1 = e.next.destination.point, e.twin.next.destination.point
        old_p0, old_p1 = e.destination.point, e.origin.point
        ret = self._triangulation.flip_edge(e)
        if ret:
            self._animation_events.append(EdgeFlipEvent(old_p0, old_p1, new_p0, new_p1))
    
    @property
    def edges(self) -> Iterable[HalfEdge]:
        return self._triangulation.edges
    
class EdgeFlipEvent(AnimationEvent):
    def __init__(self, old_p0 : Point, old_p1 : Point, new_p0 : Point, new_p1 : Point):
        self._old_p0 = old_p0
        self._old_p1 = old_p1
        self._new_p0 = new_p0
        self._new_p1 = new_p1

    def execute_on(self, data : list[Point]):
        for i in range(0, len(data)-1):
            cur = data[i]
            if isinstance(cur, PointPair):
                if cur.close_to(self._old_p0) and cur.data.close_to(self._old_p1):
                    del data[i]
                    data.append(PointPair(self._new_p0.x, self._new_p0.y, self._new_p1))
                elif cur.close_to(self._old_p1) and cur.data.close_to(self._old_p0):
                    del data[i]
                    data.append(PointPair(self._new_p0.x, self._new_p0.y, self._new_p1))
                