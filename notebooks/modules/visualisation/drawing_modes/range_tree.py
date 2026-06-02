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
        self._drawn_lines = []

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        """
        tags:
            -1 : dummy node that isn't drawn
            0 : normal node
            1 : result node
            2 : visited node
            3 : root that wasn't returned
        """
        with drawer.main_canvas.hold() and drawer.back_canvas.hold() and drawer.front_canvas.hold():
            drawer.main_canvas.clear()
            drawer.back_canvas.clear()
            drawer.front_canvas.clear()
            for point in points:
                if isinstance(point, PointTree):
                    self._drawn_lines = []
                    self.draw_x_tree(point, drawer)
                elif isinstance(point, PointList):
                    # search area box
                    drawer.front_canvas.set_colour(255, 0, 0)
                    for other in point.data:
                        drawer.front_canvas.draw_path([point, other], self._line_width, transparent=False)
                    drawer.front_canvas.set_colour(0, 0, 255)
                else:
                    #draw result points
                    drawer.front_canvas.set_colour(0, 255, 0)
                    drawer.front_canvas.draw_point(point, self._point_radius)
                    drawer.front_canvas.set_colour(0, 0, 255)

    def draw_x_tree(self, tree : PointTree,drawer: Drawer):
        if tree is None or tree.tag == -1 or tree.x in self._drawn_lines:
            return
        if tree.tag == 0:
            drawer.back_canvas.set_colour(0, 0, 255)
        elif tree.tag == 1:
            drawer.back_canvas.set_colour(0, 255, 0)
        elif tree.tag == 2:
            drawer.back_canvas.set_colour(0, 255, 255)
        elif tree.tag == 3:
            drawer.back_canvas.set_colour(255, 0, 0)
        drawer.back_canvas.draw_line(Point(tree.x, 0), Point(tree.x, 400), self._line_width)
        self._drawn_lines.append(tree.x)
        drawer.back_canvas.set_colour(0, 0, 255)
        self.draw_y_tree_points(tree.data, tree.x, drawer)

        self.draw_x_tree(tree.left, drawer)#left
        self.draw_x_tree(tree.right, drawer)#right

    def draw_y_tree_points(self, tree : PointTree, x : float, drawer: Drawer):
        if tree is None or tree.tag == -1:
            return
        if tree.tag == 0:
            drawer.main_canvas.set_colour(255, 165, 0)
        elif tree.tag == 1:
            drawer.main_canvas.set_colour(0, 255, 0)
        elif tree.tag == 2:
            drawer.main_canvas.set_colour(0, 255, 255)
        elif tree.tag == 3:
            drawer.main_canvas.set_colour(255, 0, 0)
        drawer.main_canvas.draw_point(Point(x, tree.y), self._point_radius / 2)
        drawer.main_canvas.set_colour(255, 165, 0)

        self.draw_y_tree_points(tree.left, x, drawer)
        self.draw_y_tree_points(tree.right, x, drawer)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        self.draw(drawer, points)
