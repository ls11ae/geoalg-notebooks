from __future__ import annotations
from ...geometry.animation_base import AnimationObject, AnimationEvent, AppendEvent, SetEvent, MultiEvent
from ...geometry.core import Rectangle, Point
from ...geometry import PointExtension
from typing import Iterator
from ...data_structures import EST

class RangeSearchAnimator(AnimationObject):

    def __init__(self, est : EST[int]):
        super().__init__()
        self._est = []
        for level in est.level_order():
            self._est.append([(key, 0) for key in level])
        events = []
        for point in self.points():
            events.append(AppendEvent(point))
        self._animation_events.append(MultiEvent(events))
        self._cur_level = 0
        self._cur_node = 0
        self._save_level = self._cur_level
        self._saved_node = self._cur_node

    def go_to_left_child(self):
        self._cur_level += 1
        self._cur_node *= 2

    def go_to_right_child(self):
        self._cur_level += 1
        self._cur_node *= 2
        self._cur_node += 1

    def go_to_parent(self):
        self._cur_level -=1
        self._cur_node = int(float(self._cur_node) / 2)

    def save_node(self):
        self._save_level = self._cur_level
        self._saved_node = self._cur_node

    def load_node(self):
        self._cur_level = self._save_level
        self._cur_node = self._saved_node

    def tag_cur_node(self, tag : int):
        self._est[self._cur_level][self._cur_node] = (self._est[self._cur_level][self._cur_node][0], tag)
        self._animation_events.append((SetEvent((2**self._cur_level) + self._cur_node - 1,
                                                Point(self._est[self._cur_level][self._cur_node][0], self._cur_level, tag))))

    def points(self) -> Iterator[Point]:
        points = []
        cur_level = 0
        for level in self._est:
            for tup in level:
                points.append(Point(tup[0], cur_level, tup[1]) if tup[0] is not None else None)
            cur_level += 1
        return iter(points)