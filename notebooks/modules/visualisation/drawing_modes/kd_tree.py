from __future__ import annotations
from typing import Iterable, Optional
from ..drawing import DrawingMode
from ...geometry import Point, PointNode
import math
from ...data_structures import EST

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    Point
)

class KDTreeMode(DrawingMode):
    """
    this is a very ugly fix but there just isn't another way :(
    """


    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        points = list(points)
        if any([not isinstance(node, PointNode) for node in points]):
            return
        max_level = max(points, key = lambda p : p.data[0]).data[0]
        levels = [[node for node in points if node.data[1] == i] for i in range(0, max_level + 1)]
        for level in levels:
            level.sort(key=lambda p : p.data[1])
        for i, level in enumerate(levels):
            for j, node in enumerate(level):
                if node.data[0] % 2 == 0:
                    drawer.main_canvas.draw_line(Point(node.x, 0), Point(node.x, 400), self._line_width)
                else:
                    drawer.main_canvas.draw_line(Point(0, node.y), Point(400, node.y), self._line_width)


    def _draw_animation_step(self, drawer: Drawer, points: Iterable[Point]):
        pass