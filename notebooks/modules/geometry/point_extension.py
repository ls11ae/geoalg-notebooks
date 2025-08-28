from __future__ import annotations
from .core import PointExtension, Point
from typing import Any, SupportsFloat

class PointList(PointExtension[list[Point]]):
    """A point with an additonal list of points."""
    
    def __init__(self, x: SupportsFloat, y: SupportsFloat, data : list[Point] = []):
        super().__init__(x, y, data)

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)


class PointFloat(PointExtension[float]):
    """A point with an additonal float."""

    def __init__(self, x: SupportsFloat, y: SupportsFloat, data : float = 0):
        super().__init__(x, y, data)

    def __eq__(self, other: Any) -> bool:
        return super().__eq__(other)


class PointPair(PointExtension[Point]):
    """A point with an additonal point."""

    def __init__(self, x, y, data):
        super().__init__(x, y, data)

    def __eq__(self, other):
        return super().__eq__(other)


# TODO: replace with PointExtension in all cases
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