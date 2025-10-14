from __future__ import annotations
from ..triangle_tree import Triangulation
from ...geometry import AnimationObject, AnimationEvent, Point, PointFloat, AppendEvent, PopEvent, PointPair, PointList, MultiEvent
from typing import Iterator, Iterable

from ..objects import HalfEdge, Vertex

class EdgeAnimator(AnimationObject):
    def __init__(self):
        super().__init__()
        self._illegal_edges : list[HalfEdge] = []
        self._checked_edges : list[HalfEdge] = []
        self._highlighted_edge : HalfEdge | None = None


    def highlight_triangle(self, e : HalfEdge):
        if self._highlighted_edge is not None:
            return
        self._highlighted_edge = e
        events = []
        origin = e.origin
        destination = e.destination
        opposing_point = e.next.destination
        events.append(AppendEvent(PointPair(origin.point.x, origin.point.y, destination.point, 1)))
        events.append(AppendEvent(PointPair(destination.point.x, destination.point.y, opposing_point.point, 0)))
        events.append(AppendEvent(PointPair(opposing_point.point.x, opposing_point.point.y, origin.point, 0)))
        origin = e.twin.origin
        destination = e.twin.destination
        opposing_point = e.twin.next.destination
        events.append(AppendEvent(PointPair(destination.point.x, destination.point.y, opposing_point.point, 0)))
        events.append(AppendEvent(PointPair(opposing_point.point.x, opposing_point.point.y, origin.point, 0)))
        self._animation_events.append(MultiEvent(events))

    def un_highlight_triangle(self, is_legal: bool):
        if self._highlighted_edge is not None:
            events = [PopEvent(), PopEvent(), PopEvent(), PopEvent()]
            if is_legal:
                events.append(PopEvent())
            self._animation_events.append(MultiEvent(events))
            self._highlighted_edge = None


    def _animate_circumcircle(self, e : HalfEdge):
        center = Triangulation.center_of_circumcircle(e)
        self._animation_events.append(AppendEvent(PointFloat(center.x, center.y, center.distance(e.origin.point))))
        self._animation_events.append(AppendEvent(Point(e.twin.next.destination.point.x, e.twin.next.destination.point.y)))
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())

    def _highlight_edge(self, e : HalfEdge):
        self._animation_events.append(AppendEvent(PointPair(e.origin.point.x, e.origin.point.y, e.destination.point)))

    def _unhighlight_edge(self):
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

class IncrementalConstructionAnimator(AnimationObject):
    def __init__(self, p0 : Point, p1 : Point, p2 : Point):
        super().__init__()
        self._triangulation = Triangulation(p0,p1,p2)

    def points(self) -> list[PointList]:
        return self._triangulation.to_points()
    
    def insert_point(self, p : Point):
        v = self._triangulation.insert_point(p)
        if v is None:
            return None
        else:
            self._animation_events.append(AppendEvent(Point(p.x,p.y)))
            events = []
            for e in v.outgoing_edges():
                connected_point = Point(e.destination.point.x, e.destination.point.y)
                tag = 1 if p in self._triangulation.outer_points or e.destination.point in self._triangulation.outer_points else 0
                events.append(AppendEvent(PointPair(p.x, p.y, connected_point, tag)))
            self._animation_events.append(MultiEvent(events))
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
        new_tag = 1 if new_p0 in self._triangulation.outer_points or new_p1 in self._triangulation.outer_points else 0
        ret = self._triangulation.flip_edge(e)
        if ret:
            self._animation_events.append(EdgeFlipEvent(old_p0, old_p1, new_p0, new_p1, new_tag))
    
    @property
    def edges(self) -> Iterable[HalfEdge]:
        return self._triangulation.edges
    
class EdgeFlipEvent(AnimationEvent):
    def __init__(self, old_p0 : Point, old_p1 : Point, new_p0 : Point, new_p1 : Point, new_tag : int):
        super().__init__()
        self._old_p0 = old_p0
        self._old_p1 = old_p1
        self._new_p0 = new_p0
        self._new_p1 = new_p1
        self._new_tag = new_tag

    def execute_on(self, data : list[Point]):
        for i in range(0, len(data)-1):
            cur = data[i]
            if isinstance(cur, PointPair):
                if cur.close_to(self._old_p0) and cur.data.close_to(self._old_p1):
                    del data[i]
                    data.append(PointPair(self._new_p0.x, self._new_p0.y, self._new_p1, self._new_tag))
                elif cur.close_to(self._old_p1) and cur.data.close_to(self._old_p0):
                    del data[i]
                    data.append(PointPair(self._new_p0.x, self._new_p0.y, self._new_p1, self._new_tag))
                