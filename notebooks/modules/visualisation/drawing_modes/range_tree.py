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
    Point, PointTree, PointList
)

class RangeTreeMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        drawer.front_canvas.set_colour(0, 0, 255)
        with drawer.main_canvas.hold():
            for point in points:
                if isinstance(point, PointTree):
                    self.draw_x_tree(point, 1, drawer)
                elif isinstance(point, PointList):
                    # search area box
                    drawer.front_canvas.set_colour(255, 0, 0)
                    for other in point.data:
                        drawer.front_canvas.draw_path([point, other], self._line_width, transparent=True)
                    drawer.front_canvas.set_colour(0, 0, 255)
                else:
                    drawer.front_canvas.set_colour(0, 255, 0)
                    drawer.front_canvas.draw_point(point, self._point_radius)
                    drawer.front_canvas.set_colour(0, 0, 255)


    def draw_x_tree(self, tree : PointTree, lw_factor : int, drawer: Drawer):
        if tree is None or tree.tag == -1:
            return
        drawer.back_canvas.set_colour(0, 0, 255)
        drawer.back_canvas.draw_line(Point(tree.x, 0), Point(tree.x, 400), self._line_width / lw_factor)

        drawer.main_canvas.set_colour(255, 105, 0)
        self.draw_y_tree_points(tree.data, tree.x, drawer)
        drawer.main_canvas.set_colour(0, 0, 255)
        self.draw_x_tree(tree.left, lw_factor + 1, drawer)#left
        self.draw_x_tree(tree.right, lw_factor + 1, drawer)#right

        drawer.back_canvas.set_colour(0, 0, 255)


    def draw_y_tree_points(self, tree : PointTree, x : float, drawer: Drawer):
        if tree is None or tree.tag == -1:
            return
        drawer.main_canvas.draw_point(Point(x, tree.y), self._point_radius / 2)
        self.draw_y_tree_points(tree.left, x, drawer)
        self.draw_y_tree_points(tree.right, x, drawer)

    def draw_y_tree_lines(self, tree : PointTree, x : float, lw_factor : int, drawer: Drawer):
        if tree is None or tree.tag == -1:
            return
        drawer.main_canvas.draw_line(Point(0, tree.y),Point(400, tree.y), self._point_radius / lw_factor)
        self.draw_y_tree_points(tree.left, x, drawer)
        self.draw_y_tree_points(tree.right, x, drawer)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        self.draw(drawer, points)
