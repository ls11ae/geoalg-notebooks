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