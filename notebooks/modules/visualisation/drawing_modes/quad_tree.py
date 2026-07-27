from __future__ import annotations
from typing import Optional, Iterable

from ..drawing import DrawingMode, DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, Drawer
from ... import PointExtension
from ...data_structures import Quadtree
from ...geometry import Point, Rectangle, AnimationEvent, AnimationObject
from enum import Enum
from ...data_structures import QuadTreeAnimator


class QuadTreeMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS,
                 line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        points = list(points)
        if len(points) < 1:
            return
        point = points[0]
        if not isinstance(point, PointExtension):
            return
        quadtree = point.data
        if not isinstance(quadtree, Quadtree):
            return
        with drawer.main_canvas.hold():
            self._draw_quadtree(quadtree, drawer)


    def _draw_quadtree(self, quadtree : Quadtree, drawer : Drawer):
        if quadtree is None:
            return
        if quadtree.area is None:
            return
        if quadtree.NW is None and quadtree.NE is None and quadtree.SW is None and quadtree.SE is None:
            return
        center_x = (quadtree.area.right - quadtree.area.left) / 2  + quadtree.area.left
        center_y = (quadtree.area.upper - quadtree.area.lower) / 2 + quadtree.area.lower
        drawer.main_canvas.draw_path([Point(center_x, quadtree.area.upper), Point(center_x, quadtree.area.lower)], self._line_width)
        drawer.main_canvas.draw_path([Point(quadtree.area.left, center_y), Point(quadtree.area.right, center_y)], self._line_width)
        self._draw_quadtree(quadtree.NW, drawer)
        self._draw_quadtree(quadtree.NE, drawer)
        self._draw_quadtree(quadtree.SW, drawer)
        self._draw_quadtree(quadtree.SE, drawer)


    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        self.draw(drawer, points)