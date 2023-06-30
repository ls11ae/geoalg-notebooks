from __future__ import annotations
import copy
from itertools import chain
from typing import Any, Iterable, Iterator, Optional
import numpy as np

from geometry import LineSegment, Point

class VerticalDecomposition:
    def __init__(self, segements: set(LineSegment)) -> None:
        pass

    @classmethod
    def build_vertical_decomposition(cls, segements: set(LineSegment)) -> VerticalDecomposition:
        # randomized incremental construction
        # TODO: also need search structure
        pass

class FaceVD: # This is the trapezoid
    def __init__(self) -> None:
        self._top_linesegemnt: LineSegmentVD = None
        self._bottom_linesegment: LineSegmentVD = None
        self._left_point: Point = None
        self._right_point: Point = None
        self._neighbors = [] # Up to four neigboring faces (no degenerate cases)

class LineSegmentVD(LineSegment):
    def __init__(self, p: Point, q: Point):
        super().__init__(p, q)
        self._above_dcel_face = None

        @property
        def above_face(self) -> Any: # TODO: return type needs to be a face of a DCEL
            return self._above_dcel_face
