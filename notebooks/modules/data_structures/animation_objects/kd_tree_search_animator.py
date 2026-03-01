from __future__ import annotations

from ...geometry import Point, PointFloat, AnimationObject, AppendEvent, SetEvent, MultiEvent, Rectangle, PopEvent
from typing import Iterator, Optional
from .kd_tree_construction_animator import KDTreeConstructionAnimator

class KDTreeSearchAnimator(AnimationObject):

    def __init__(self, kdc : KDTreeConstructionAnimator, search_area : Rectangle, starting_area : Rectangle):
        super().__init__()
        self._nodes = []
        for point in kdc.points():
            if isinstance(point, PointFloat):
                self._nodes.append(point)
        point_events = []
        for point in self._nodes:
            if isinstance(point, PointFloat):
                point_events.append(PointFloat(point.x, point.y, point.data, 0))
        self._animation_events = [MultiEvent(point_events)]
        self._points = []
        self._search_region : Rectangle = search_area
        self._current_region : Rectangle = starting_area

    def add_point(self, point : Point):
        self._points.append(Point(point.x, point.y, 0))
        self._animation_events.append(AppendEvent(Point(point.x, point.y, 0)))

    def set_search_region(self, region : Rectangle):
        if self._search_region is None:
            self._animation_events = [MultiEvent(self._animation_events)]
            self._animation_events.append(MultiEvent([AppendEvent(point) for point in region.points()]))
            self._search_region = region

    def set_current_region(self, region : Rectangle):
        if self._current_region is None:
            self._animation_events.append(MultiEvent([AppendEvent(point) for point in region.points()]))
            self._current_region = region
        elif not self._current_region.__eq__(region):
            self._animation_events.append(MultiEvent([PopEvent() for _ in region.points()]))
            self._animation_events.append(MultiEvent([AppendEvent(point) for point in region.points()]))
            self._current_region = region

    def points(self) -> Iterator[Point]:
        print(self._points)
        return iter(self._nodes + self._points)