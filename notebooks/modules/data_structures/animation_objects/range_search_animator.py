from __future__ import annotations
from ...geometry.animation_base import AnimationObject, AppendEvent, SetEvent, MultiEvent
from ...geometry.core import Rectangle, Point
from ...geometry import PointExtension
from typing import Iterator
from ...data_structures import EST

class RangeSearchAnimator(AnimationObject):

    def __init__(self, est : EST):
        super().__init__()
        self._est = []
        for level in est.level_order():
            self._est.append([(key, 0) for key in level])
        self._cur_level = 0
        self._cur_node = 0

    def go_to_left_child(self):
        self._cur_level += 1
        self._cur_node *= 2

    def go_to_right_child(self):
        self._cur_level += 1
        self._cur_node *= 2
        self._cur_node += 1

    def tag_cur_node(self, tag : int):
        self._est[self._cur_level][self._cur_node] = (self._est[self._cur_level][self._cur_node][0], tag)

    def points(self) -> Iterator[Point]:
        points = []
        cur_level = 0
        for level in self._est:
            for tup in level:
                points.append(Point(tup[0], cur_level, tup[1]))
            cur_level += 1
        return iter(points)
