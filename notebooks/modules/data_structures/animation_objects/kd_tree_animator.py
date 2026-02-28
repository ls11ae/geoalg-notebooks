from __future__ import annotations

from ...geometry import Point, PointFloat, AnimationObject, AppendEvent, SetEvent, MultiEvent, Rectangle, PopEvent
from typing import Iterator, Optional
from .kd_tree_construction_animator import KDTreeConstructionAnimator

class KDTreeSearchAnimator(AnimationObject):

    def __init__(self, kdc : KDTreeConstructionAnimator):
        super().__init__()
        self._animation_events = [MultiEvent(kdc.animation_events())]
        self._index = 0
        self._saved_index = 0
        self._nodes : list[PointFloat] = []
        self._search_region : Optional[Rectangle] = None
        self._current_region : Optional[Rectangle] = None

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

    def save_node(self):
        self._saved_index = self._index

    def load_node(self):
        self._index = self._saved_index

    def add_node(self, point : Point):
        self._nodes.append(PointFloat(point.x, point.y, self._index))
        self._animation_events.append(AppendEvent(PointFloat(point.x, point.y, self._index)))

    def tag_cur_node(self, tag : int):
        for i, node in enumerate(self._nodes):
            if node.data is self._index:
                node.tag = tag
                self._animation_events.append(SetEvent(i, node))

    def tag_all(self, tag : int):
        for node in self._nodes:
            node.tag = tag

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
        return iter(self._nodes + (self._search_region.points() if self._search_region else []))