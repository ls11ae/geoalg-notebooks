from __future__ import annotations
from collections import deque
from .core import PointExtension, Point
from typing import Any, SupportsFloat, Optional


class PointList(PointExtension[list[Point]]):
    """A point with an additional list of points."""
    
    def __init__(self, x: SupportsFloat, y: SupportsFloat, data : list[Point], tag : int = 0):
        super().__init__(x, y, data, tag)

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)


class PointFloat(PointExtension[float]):
    """A point with an additional float."""

    def __init__(self, x: SupportsFloat, y: SupportsFloat, data : float = 0, tag : int = 0):
        super().__init__(x, y, data, tag)

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)


class PointPair(PointExtension[Point]):
    """A point with an additional point."""

    def __init__(self, x, y, data, tag = 0):
        super().__init__(x, y, data, tag)

    def __eq__(self, other):
        return super().__eq__(other)

class PointNode(PointExtension[tuple[int,int]]):
    """A point with an additional tuple for layer and node number in a binary tree"""

    def __init__(self, x: SupportsFloat, y: SupportsFloat, data: tuple[int,int]):
        super().__init__(x, y, data)

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)

class PointTree(PointExtension):
    """A binary tree but points"""

    def __init__(self, x: SupportsFloat, y: SupportsFloat, parent : Optional[PointTree], data):
        super().__init__(x, y, data)
        self._left : Optional[PointTree] = None
        self._right : Optional[PointTree] = None
        self._parent : Optional[PointTree] = parent

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)

    @property
    def left(self) -> Optional[PointTree]:
        return self._left

    @property
    def right(self) -> Optional[PointTree]:
        return self._right

    @property
    def parent(self) -> Optional[PointTree]:
        return self._parent

    @left.setter
    def left(self, new_left : PointTree):
        self._left = new_left
        new_left._parent = self

    @right.setter
    def right(self, new_right: PointTree):
        self._right = new_right
        new_right._parent = self

    @parent.setter
    def parent(self, new_parent : PointTree):
        self._parent = new_parent

    def level_order(self):
        if self is None:
            return
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            if node._left is not None:
                queue.append(node._left)
            if node._right is not None:
                queue.append(node._right)

'''
references a point in a list by storing the list and the position

overwrites the x, y, _x, _y properties from point to make sure operations from point class access
correct values. This is necessary because the x/y paramter of the point class get never set because
the super().__init__ method is never called

(do not use)
'''
class PointReference(Point):    
    def __init__(self, container: list[Point], position: int):
        self._container = container
        self._position = position

    @property
    def container(self) -> list[Point]:
        return self._container

    @property
    def position(self) -> int:
        return self._position

    @property
    def point(self) -> Point:
        return self._container[self._position]

    @property
    def x(self) -> float:
        return self.point.x

    @property
    def y(self) -> float:
        return self.point.y

    @property
    def _x(self) -> float:
        return self.point.x

    @property
    def _y(self) -> float:
        return self.point.y
    
    def copy(self) -> PointReference:
        return PointReference([point.copy() for point in self.container], self._position)