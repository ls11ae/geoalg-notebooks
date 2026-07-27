from typing import Optional
from ..geometry import Point, Rectangle


class Quadtree:
    def __init__(self):
        self.NE : Optional[Quadtree] = None
        self.NW : Optional[Quadtree] = None
        self.SE : Optional[Quadtree] = None
        self.SW : Optional[Quadtree] = None
        self.PARENT : Optional[Quadtree] = None
        self.points : list[Point] = []
        self.area : Optional[Rectangle] = None

    @property
    def isDummy(self) -> bool:
        return self.area is None

    @property
    def isLeaf(self) -> bool:
        return (self.NE is None and
                self.NW is None and
                self.SE is None and
                self.SW is None)
