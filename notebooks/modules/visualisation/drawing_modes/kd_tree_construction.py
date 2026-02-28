from __future__ import annotations
from typing import Iterable, Optional
from ..drawing import DrawingMode
from ...geometry import Point, PointFloat
import math
from ...data_structures import EST

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    Point
)

class KDTreeConstructionMode(DrawingMode):
    """
    this is a very ugly fix but there just isn't another way :(
    """


    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
        self._points = None

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        nodes = []
        others = []
        for point in points:
            if isinstance(point, PointFloat):
                nodes.append(point)
            elif point:
                others.append(point)
        with drawer.main_canvas.hold():
            if nodes:
                max_index = max(nodes, key=lambda p : p.data).data
                point_heap = [None for _ in range(0, max_index + 1)]
                for node in nodes:
                    point_heap[node.data] = node
                self._points = point_heap
                drawer.main_canvas.clear()
                self._recursive_draw(drawer, 0,0, 400, 0, 400, 0)

            for point in others:
                if point:
                    drawer.main_canvas.set_colour(255,0,0)
                    drawer.main_canvas.draw_point(point, self._point_radius)
                    drawer.main_canvas.set_colour(0, 0, 255)
        self._points = None

    def _recursive_draw(self, drawer, index,
                        left, right, lower, upper, level):
        if index >= len(self._points) or self._points[index] is None:
            return
        cur_node = self._points[index]
        lc_index = 2 * index + 1
        rc_index = 2 * index + 2
        if level % 2 == 0:
            if cur_node.tag == 1:
                drawer.main_canvas.draw_path(
                    [Point(cur_node.x, lower), Point(cur_node.x, upper)],
                    self._line_width
                )
                self._recursive_draw(drawer, lc_index,
                                 left, cur_node.x, lower, upper, level + 1)
                self._recursive_draw(drawer, rc_index,
                                 cur_node.x, right, lower, upper, level + 1)
        else:
            if cur_node.tag == 1:
                drawer.main_canvas.draw_path(
                    [Point(left, cur_node.y), Point(right, cur_node.y)],
                    self._line_width
                )
                self._recursive_draw(drawer, lc_index,
                                     left, right, lower, cur_node.y, level + 1)
                self._recursive_draw(drawer, rc_index,
                                         left, right, cur_node.y, upper, level + 1)


    def _draw_animation_step(self, drawer: Drawer, points: Iterable[Point]):
        self.draw(drawer, points)