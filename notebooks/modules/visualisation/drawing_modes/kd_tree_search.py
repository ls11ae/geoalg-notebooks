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

COLOR_SCHEME1 = [0,0,255], [255,0,0]

class KDTreeSearchMode(DrawingMode):
    """
    this is a very ugly fix but there just isn't another way :(
    """


    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
        self._points = None
        self._color_scheme = COLOR_SCHEME1

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        nodes = []
        others = []
        for point in points:
            if isinstance(point, PointFloat):
                nodes.append(point)
            else:
                others.append(point)
        max_index = max(nodes, key=lambda p : p.data).data
        point_heap = [None for _ in range(0, max_index + 1)]
        for point in nodes:
            point_heap[point.data] = point
        self._points = point_heap
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            self._recursive_draw(drawer, 0,0, 400, 0, 400, 0)
            for point in nodes:
                if point.tag == 1:
                    self._set_node_color(drawer, point.tag)
                    drawer.main_canvas.draw_point(point, self._point_radius)
                    self._set_node_color(drawer, 0)
            self._set_node_color(drawer, 1)
            if len(others) >= 4:
                drawer.main_canvas.draw_path(others[0:4], self._line_width, close=True, transparent=True)
            if len(others) >= 8:
                drawer.main_canvas.draw_path(others[4:8], self._line_width, close=True)
            self._set_node_color(drawer, 0)
        self._points = None


    def _recursive_draw(self, drawer, index,
                        left, right, lower, upper, level):
        if index >= len(self._points) or self._points[index] is None:
            return
        cur_node = self._points[index]
        if level % 2 == 0:
            drawer.main_canvas.draw_path(
                [Point(cur_node.x, lower), Point(cur_node.x, upper)],
                self._line_width
            )
            self._recursive_draw(drawer, 2 * index + 1,
                                 left, cur_node.x, lower, upper, level + 1)
            self._recursive_draw(drawer, 2 * index + 2,
                                 cur_node.x, right, lower, upper, level + 1)
        else:
            drawer.main_canvas.draw_path(
                [Point(left, cur_node.y), Point(right, cur_node.y)],
                self._line_width
            )
            self._recursive_draw(drawer, 2 * index + 2,
                                 left, right, cur_node.y, upper, level + 1)
            self._recursive_draw(drawer, 2 * index + 1,
                                 left, right, lower, cur_node.y, level + 1)

    def _set_node_color(self, drawer : Drawer, tag : int):
        drawer.main_canvas.set_colour(self._color_scheme[tag][0], self._color_scheme[tag][1], self._color_scheme[tag][2])

    def _draw_animation_step(self, drawer: Drawer, points: Iterable[Point]):
        self.draw(drawer, points)