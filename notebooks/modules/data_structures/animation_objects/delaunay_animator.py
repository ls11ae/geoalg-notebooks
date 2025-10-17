from __future__ import annotations
from ..triangle_tree import Triangulation
from ...geometry import AnimationObject, AnimationEvent, Point, PointFloat, AppendEvent, PopEvent, PointPair, PointList, MultiEvent, DeleteAtEvent
from typing import Iterator, Iterable

from ..objects import HalfEdge, Vertex, Face

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
    def edges(self) -> list[HalfEdge]:
        return self._triangulation.edges

    @property
    def faces(self) -> list[Face]:
        return self._triangulation.faces

    @property
    def outer_face(self) -> Face:
        return self._triangulation.outer_face




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
                