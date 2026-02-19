from __future__ import annotations
from typing import Iterable, Optional
from .binary_tree import BinaryTreeMode
import math
from ...data_structures import EST

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    Point
)

class RangeSearchMode(BinaryTreeMode):
    """
    this is a very ugly fix but there just isn't another way :(
    """
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        level_order = []
        cur_level = []
        nodes_on_level = 2**len(level_order)
        for point in points:
            if len(cur_level) >= nodes_on_level:
                level_order.append(cur_level)
                cur_level = [point]
                nodes_on_level = 2 ** len(level_order)
            else:
                cur_level.append(point)
        if cur_level:
            level_order.append(cur_level)
        self._draw_tree(drawer, level_order)