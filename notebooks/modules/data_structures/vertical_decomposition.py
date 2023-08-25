from __future__ import annotations
from abc import ABC, abstractmethod
import copy
from itertools import chain
from typing import Any, Iterable, Iterator, Optional
import numpy as np

from ..geometry import LineSegment, Point, Orientation as ORT, Rectangle
from .objects import Face
from .binary_tree import BinaryTree
from .dcel import DoublyConnectedEdgeList


class PointLocation:
    def __init__(self, bounding_box: Rectangle, segments: set[LineSegment] = []) -> None:
        self._vertical_decomposition = VerticalDecomposition(bounding_box)
        initial_face = self._vertical_decomposition._trapezoids[0]
        self._search_structure = VDSearchStructure(initial_face)

    #@classmethod
    #def build_vertical_decomposition(cls, segments: set[LineSegment]) -> VerticalDecomposition:
    #    # randomized incremental construction
    #    pass


class VerticalDecomposition:
    def __init__(self, bounding_box: Rectangle) -> None:
        self._bounding_box = bounding_box
        self._trapezoids: list(VDFace) = []
        # bounding box points
        upper_left = Point(bounding_box.left, bounding_box.upper)
        upper_right = Point(bounding_box.right, bounding_box.upper)
        lower_left = Point(bounding_box.left, bounding_box.lower)
        lower_right = Point(bounding_box.right, bounding_box.lower)
        top = VDLineSegment(upper_left, upper_right)
        bottom = VDLineSegment(lower_left, lower_right)
        dcel = DoublyConnectedEdgeList()
        bottom._above_dcel_face = dcel.outer_face
        initial_trapezoid = VDFace(top, bottom, upper_left, upper_right)
        self._trapezoids.append(initial_trapezoid)


class VDNode(ABC):
    def __init__(self) -> None:
        self._left: Optional[VDNode] = None
        self._right: Optional[VDNode] = None

    @abstractmethod
    def search(self, point: Point) -> VDFace:
        pass


class VDXNode(VDNode):
    def __init__(self, point: Point) -> None:
        super().__init__()
        self._point: Point = point

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    def search(self, point: Point) -> VDFace:
        if point.x < self._point.x:
            return self._left.search(point)
        else:  # equality not possible in general position TODO: Make Robust using symbolic shear transform
            return self._right.search(point)


class VDYNode(VDNode):
    def __init__(self, line_segment: VDLineSegment) -> None:
        super().__init__()
        self._line_segment = line_segment

    @property
    def lower(self):
        return self._left

    @property
    def upper(self):
        return self._right

    def search(self, point: Point) -> VDFace:
        cr = point.orientation(self._line_segment.left, self._line_segment.right)
        if cr == ORT.LEFT:
            return self.upper.search(point)
        elif cr == ORT.RIGHT:
            return self.lower.search(point)
        else:
            raise RuntimeError(f"Point {point} must not lie on line induced by the line segment {self._line_segment}")


class VDLeaf(VDNode):
    def __init__(self, face: VDFace) -> None:
        self._face: VDFace = face
        self._face.search_leaf = self
        self._left = None
        self._right = None

    def search(self, point: Point) -> VDFace:
        return self._face


class VDSearchStructure:
    def __init__(self, initial_face: VDFace) -> None:
        self._root: VDNode = VDLeaf(initial_face)

    def search(self, point: Point) -> Face:
        vd_face = self._root.search(point)
        dcel_face = vd_face._bottom_line_segment.above_face
        return dcel_face


class VDFace:  # the trapezoid
    def __init__(self, top_ls: VDLineSegment, bottom_ls: VDLineSegment, leftp: Point, rightp: Point) -> None:
        self._top_line_segment: VDLineSegment = top_ls
        self._bottom_line_segment: VDLineSegment = bottom_ls
        self._left_point: Point = leftp
        self._right_point: Point = rightp
        self._search_leaf = None

    @property
    def search_leaf(self):
        return self._search_leaf
    
    @search_leaf.setter
    def search_leaf(self, search_leaf):
        self._search_leaf = search_leaf



class VDLineSegment(LineSegment):
    def __init__(self, p: Point, q: Point):
        super().__init__(p, q)
        self._above_dcel_face: Optional[Face] = None  # The original face of the planar subdivision (DCEL)

    @property
    def above_face(self) -> Face:
        return self._above_dcel_face
