from __future__ import annotations

from ...geometry import Point, PointFloat, AnimationObject, AppendEvent, SetEvent, MultiEvent, Rectangle, DeleteAtEvent
from typing import Iterator, Optional
from .kd_tree_construction_animator import KDTreeConstructionAnimator

class KDTreeSearchAnimator(AnimationObject):

    def __init__(self, kdc : KDTreeConstructionAnimator, search_region : Rectangle, current_region : Rectangle):
        super().__init__()
        self._nodes = []
        for point in kdc.points():
            if isinstance(point, PointFloat):
                self._nodes.append(point)
        point_events = []
        point_events.extend([AppendEvent(Point(point.x, point.y, 2)) for point in current_region.points()])
        point_events.extend([AppendEvent(Point(point.x, point.y, 1)) for point in search_region.points()])
        for point in self._nodes:
            point_events.append(AppendEvent(PointFloat(point.x, point.y, point.data, point.tag)))
        self._animation_events = [MultiEvent(point_events)]
        self._points = []
        self._search_region : Rectangle = search_region
        self._current_region : Rectangle = current_region

    def add_point(self, point : Point):
        self._points.append(Point(point.x, point.y, 0))
        self._animation_events.append(AppendEvent(Point(point.x, point.y, 0)))

    def set_current_region(self, region : Rectangle):
        if region:
            events = []
            for i, point in enumerate(region.points()):
                events.append(SetEvent(i, Point(point.x, point.y, 2)))
            self._animation_events.append(MultiEvent(events))
        else:
            self._animation_events.append(MultiEvent([SetEvent(i, None) for i in range(4)]))

    def points(self) -> Iterator[Point]:
        return iter(self._nodes + self._points)