from __future__ import annotations

from abc import ABC
from typing import Optional, Iterator
from ...geometry import Point, Rectangle, AnimationEvent, AnimationObject, PointExtension
from enum import Enum
from ..quadtree import Quadtree

class Direction(Enum):
    NW = 0
    NE = 1
    SW = 2
    SE = 3

class Path:
    def __init__(self):
        self._directions : list[Direction] = []

    def nw(self):
        self._directions.append(Direction.NW)

    def ne(self):
        self._directions.append(Direction.NE)

    def sw(self):
        self._directions.append(Direction.SW)

    def se(self):
        self._directions.append(Direction.SE)

    def parent(self):
        if self._directions:
            self._directions.pop()

    def __copy__(self):
        copy = Path()
        for direction in self._directions:
            copy._directions.append(direction)
        return copy


class QuadTreeAnimator(AnimationObject):

    def __init__(self):
        super().__init__()
        self._root : Quadtree = Quadtree()
        self._cur : Quadtree = self._root
        self._path : Path = Path()

    def nw(self):
        if self._cur.NW is None:
            self._cur.NW = Quadtree()
            self._cur.NW.PARENT = self._cur
            self._cur = self._cur.NW
        self._path.nw()

    def ne(self):
        if self._cur.NE is None:
            self._cur.NE = Quadtree()
            self._cur.NE.PARENT = self._cur
            self._cur = self._cur.NE
        self._path.ne()

    def sw(self):
        if self._cur.SW is None:
            self._cur.SW = Quadtree()
            self._cur.SW.PARENT = self._cur
            self._cur = self._cur.SW
        self._path.sw()

    def se(self):
        if self._cur.SE is None:
            self._cur.SE = Quadtree()
            self._cur.SE.PARENT = self._cur
            self._cur = self._cur.SE
        self._path.se()

    def parent(self):
        if self._cur.PARENT:
            self._cur = self._cur.PARENT
            self._path.parent()

    def set_node(self, points : list[Point], area : Rectangle):
        self._cur.points = points
        self._cur.area = area
        self._animation_events.append(UpdateNodeEvent(points, area, self._path.__copy__()))

    def points(self) -> Iterator[Point]:
        return iter([PointExtension(0,0,self._root, 0)])


class UpdateNodeEvent(AnimationEvent):
    def __init__(self, points: list[Point], area: Rectangle, path : Path):
        super().__init__()
        self._node = Quadtree()
        self._node.points = points
        self._node.area = area
        self._path = path

    def execute_on(self, data : list[Point]):
        if len(data) == 0:#no root point created yet
            data.append(PointExtension(0,0,self._node, 0))
            return
        root_point = data[0]
        if not isinstance(root_point, PointExtension):
            return
        root = data[0].data
        if not isinstance(root, Quadtree):
            return
        cur = root
        for direction in self._path._directions[:-1]:
            match direction:
                case Direction.NW:
                    cur = cur.NW
                case Direction.NE:
                    cur = cur.NE
                case Direction.SW:
                    cur = cur.SW
                case Direction.SE:
                    cur = cur.SE
            if cur is None:
                return
        match self._path._directions[-1]:
            case Direction.NW:
                if cur.NW is None:
                    cur.NW = self._node
                    self._node.PARENT = cur
            case Direction.NE:
                if cur.NE is None:
                    cur.NE = self._node
                    self._node.PARENT = cur
            case Direction.SW:
                if cur.SW is None:
                    cur.SW = self._node
                    self._node.PARENT = cur
            case Direction.SE:
                if cur.SE is None:
                    cur.SE = self._node
                    self._node.PARENT = cur
