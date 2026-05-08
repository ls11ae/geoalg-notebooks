from __future__ import annotations

from ...geometry.animation_base import AnimationObject, AnimationEvent, AppendEvent, MultiEvent
from ...geometry import Point, PointList
from ...geometry import PointTree
from typing import Iterator
from enum import Enum
from ...data_structures import EST


class TreeDirection(Enum):
    LEFT = 0
    RIGHT = 1
    PARENT = 2

class TreePath:
    def __init__(self):
        self.path : list[TreeDirection] = []

    def reset(self):
        self.path = []

    def left(self):
        self.path.append(TreeDirection.LEFT)

    def right(self):
        self.path.append(TreeDirection.RIGHT)

    def parent(self):
        if len(self.path) > 0 and self.path[-1] is not TreeDirection.PARENT:
            self.path.pop()
        else:
            self.path.append(TreeDirection.PARENT)

    def copy(self) -> TreePath:
        copy = TreePath()
        for direction in self.path:
            copy.path.append(direction)
        return copy

class RangeTreeAnimator(AnimationObject):

    def __init__(self):
        super().__init__()
        self._cur_y = PointTree(0, 0, None, data=None)
        self._cur_y.tag = -1
        self._root = PointTree(0, 0, None, data=self._cur_y)
        self._root.tag = -1
        self._cur_x = self._root
        self._x_path = TreePath()
        self._y_path = TreePath()

        self._search_bounds = []
        self._result = []

        self._saved_x = None
        self._saved_x_path = None

    def save_x(self):
        self._saved_x = self._cur_x
        self._saved_x_path = self._x_path.copy()

    def load_x(self):
        if self._saved_x is None:
            return
        self._cur_x = self._saved_x
        self._x_path = self._saved_x_path


    def set_cur_x(self, point : Point, tag : int):
        self._cur_x.x = point.x
        self._cur_x.y = point.y
        self._cur_x.tag = tag
        self._animation_events.append(SetXNodeEvent(self._x_path.path, Point(point.x, point.y, tag)))

    def tag_cur_x(self, tag : int):
        self._cur_x.tag = tag
        self._animation_events.append(SetXNodeEvent(self._x_path.path, Point(self._cur_x.x, self._cur_x.y, tag)))

    def go_to_left_child_x(self):
        if self._cur_x.left is None:
            self._cur_x.left = PointTree(0, 0, self._cur_x, None)
            self._cur_x.left.tag = -1
        self._cur_x = self._cur_x.left
        self._x_path.left()
        if self._cur_x.data is None:
            self._cur_x.data = PointTree(0, 0, None, None)
            self._cur_x.data.tag = -1
        self._cur_y = self._cur_x.data
        self._y_path.reset()

    def go_to_right_child_x(self):
        if self._cur_x.right is None:
            self._cur_x.right = PointTree(0, 0, self._cur_x, None)
            self._cur_x.right.tag = -1
        self._cur_x = self._cur_x.right
        self._x_path.right()
        if self._cur_x.data is None:
            self._cur_x.data = PointTree(0, 0, None, None)
            self._cur_x.data.tag = -1
        self._cur_y = self._cur_x.data
        self._y_path.reset()

    def go_to_parent_x(self):
        if self._cur_x.parent is not None:
            self._cur_x = self._cur_x.parent
            self._cur_y = self._cur_x.data
            self._x_path.parent()

    def set_cur_y(self, point: Point, tag: int):
        self._cur_y.x = point.x
        self._cur_y.y = point.y
        self._cur_y.tag = tag
        self._animation_events.append(SetYNodeEvent(self._x_path.path,self._y_path.path, Point(point.x, point.y, tag)))

    def tag_cur_y(self, tag : int):
        self._cur_y.tag = tag
        self._animation_events.append(SetYNodeEvent(self._x_path.path, self._y_path.path, Point(self._cur_y.x, self._cur_y.y, tag)))
        
    def go_to_left_child_y(self):
        if self._cur_y.left is None:
            self._cur_y.left = PointTree(0, 0, self._cur_y, None)
            self._cur_y.left.tag = -1
        self._cur_y = self._cur_y.left
        self._y_path.left()


    def go_to_right_child_y(self):
        if self._cur_y.right is None:
            self._cur_y.right = PointTree(0, 0, self._cur_y, None)
            self._cur_y.right.tag = -1
        self._cur_y = self._cur_y.right
        self._y_path.right()

    def go_to_parent_y(self):
        if self._cur_y.parent is not None:
            self._cur_y = self._cur_y.parent
            self._y_path.parent()

    def reset_paths(self):
        self._x_path.reset()
        self._y_path.reset()

    def set_search_bounds(self, lower_x : int, upper_x : int, lower_y : int, upper_y : int):
        p_ll = PointList(lower_x, lower_y, [Point(lower_x, upper_y), Point(upper_x, lower_y)])
        p_ur = PointList(upper_x, upper_y, [Point(lower_x, upper_y), Point(upper_x, lower_y)])
        self._animation_events.append(MultiEvent([AppendEvent(p_ll), AppendEvent(p_ur)]))
        self._search_bounds = [p_ll, p_ur]

    def set_search_result(self, points : list[Point]):
        self._result = points

    def points(self) -> Iterator[Point]:
        return iter([self._root] + self._search_bounds + self._result)


class SetXNodeEvent(AnimationEvent):
    def __init__(self, path : list[TreeDirection], node : Point):
        super().__init__()
        self._path = path
        self._node = node

    def execute_on(self, data: list[Point]):
        if len(data) == 0:
            # handle empty list by creating root
            root = PointTree(self._node.x, self._node.y, None, PointTree(0,0,None,None))
            root.tag = self._node.tag
            root.data.tag = -1
            data.append(root)
            return
        root = data[0]
        if not isinstance(root, PointTree):
            return
        if len(self._path) == 0:
            # handle empty path by updating root
            root.x = self._node.x
            root.y = self._node.y
            root.tag = self._node.tag
            return
        # root exists and is not the target
        target = get_node(root, self._path[:-1])
        if self._path[-1] == TreeDirection.LEFT:
            if target.left is None:
                target.left = PointTree(self._node.x, self._node.y, None, PointTree(0,0,None,None))
                target.left.tag = self._node.tag
                target.left.data.tag = -1
            else:
                target.left.x = self._node.x
                target.left.y = self._node.y
                target.left.tag = self._node.tag
        elif self._path[-1] == TreeDirection.RIGHT:
            if target.right is None:
                target.right = PointTree(self._node.x, self._node.y, None, PointTree(0,0,None,None))
                target.right.tag = self._node.tag
                target.left.data.tag = -1
            else:
                target.right.x = self._node.x
                target.right.y = self._node.y
                target.right.tag = self._node.tag

class SetYNodeEvent(AnimationEvent):
    def __init__(self, x_path : list[TreeDirection], y_path : list[TreeDirection], node : Point):
        super().__init__()
        self._x_path = x_path
        self._y_path = y_path
        self._node = node

    def execute_on(self, data : list[Point]):
        root = data[0]
        if not isinstance(root, PointTree):
            return
        y_root = get_node(root, self._x_path).data
        if not isinstance(y_root, PointTree):
            return
        if len(self._y_path) == 0:
            # handle empty path by updating root
            y_root.x = self._node.x
            y_root.y = self._node.y
            y_root.tag = self._node.tag
            return
        # root exists and is not the target
        y_target = get_node(y_root, self._y_path[:-1])
        if self._y_path[-1] == TreeDirection.LEFT:
            if y_target.left is None:
                y_target.left = PointTree(self._node.x, self._node.y, None, None)
                y_target.left.tag = self._node.tag
            else:
                y_target.left.x = self._node.x
                y_target.left.y = self._node.y
                y_target.left.tag = self._node.tag
        elif self._y_path[-1] == TreeDirection.RIGHT:
            if y_target.right is None:
                y_target.right = PointTree(self._node.x, self._node.y, None, None)
                y_target.right.tag = self._node.tag
            else:
                y_target.right.x = self._node.x
                y_target.right.y = self._node.y
                y_target.right.tag = self._node.tag

def get_node(root : PointTree, path : list[TreeDirection]) -> PointTree:
    cur = root
    for direction in path:
        if direction == TreeDirection.LEFT:
            cur = cur.left
        elif direction == TreeDirection.RIGHT:
            cur = cur.right
        elif direction == TreeDirection.PARENT:
            cur = cur.parent
    return cur