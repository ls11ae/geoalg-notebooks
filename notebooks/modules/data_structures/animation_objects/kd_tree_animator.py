from __future__ import annotations
from ...geometry import Point, PointNode, AnimationObject, AppendEvent, SetEvent, MultiEvent
from typing import Iterator
from ...data_structures import EST

class KDTreeAnimator(AnimationObject):

    def __init__(self):
        super().__init__()
        self._cur_level = 0
        self._cur_node = 0
        self._save_level = self._cur_level
        self._saved_node = self._cur_node
        self._nodes : list[PointNode] = []

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

    def add_node(self, point : Point):
        p = PointNode(point.x, point.y, (self._cur_level, self._cur_node))
        self._nodes.append(p)
        self._animation_events.append(AppendEvent(p))

    def tag_cur_node(self, tag : int):
        pass

    def points(self) -> Iterator[Point]:
        return iter(self._nodes)