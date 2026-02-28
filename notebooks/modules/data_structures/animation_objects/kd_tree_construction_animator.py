from __future__ import annotations

from ...geometry import Point, PointFloat, AnimationObject, AppendEvent, MultiEvent, SetEvent, PopEvent
from typing import Iterator

class KDTreeConstructionAnimator(AnimationObject):

    def __init__(self):
        super().__init__()
        self._index = 0
        self._nodes : list[PointFloat] = []
        self._point_count = 0

    def go_to_left_child(self):
        self._index *= 2
        self._index += 1

    def go_to_right_child(self):
        self._index *= 2
        self._index += 2

    def go_to_parent(self):
        if self._index % 2 == 0:
            self._index -=2
        else:
            self._index -= 1
        self._index  = int(self._index / 2)

    def add_leaf(self, point : Point):
        self._nodes.append(PointFloat(point.x, point.y, self._index, 0))
        AppendEvent(PointFloat(point.x, point.y, self._index, 0))

    def add_inner_node(self, point : Point):
        self._nodes.append(PointFloat(point.x, point.y, self._index, 1))
        self._animation_events.append(AppendEvent(PointFloat(point.x, point.y, self._index, 1)))

    def set_current_points(self, points : list[Point]):
        if self._point_count == 0:
            self._animation_events.append(MultiEvent([AppendEvent(point) for point in points]))
            self._point_count = len(points)
        events = []
        for i in range(self._point_count):
            if i < len(points):
                events.append(SetEvent(i, Point(points[i].x, points[i].y)))
            else:
                events.append(SetEvent(i, None))
        self._animation_events.append(MultiEvent(events))

    def points(self) -> Iterator[Point]:
        return iter(self._nodes)