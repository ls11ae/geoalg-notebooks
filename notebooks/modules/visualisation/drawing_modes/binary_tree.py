from __future__ import annotations
from typing import Iterable, Optional
import math
from ...data_structures import EST

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    Point
)

COLOR_SCHEME = [255, 165, 0], [0,0,255], [0,255,0], [255,0,0], [244,109,67], [253,174,97], [254,224,144], [171,217,233], [116,173,209], [69,117,180], [49,54,149]

class BinaryTreeMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
        self.binary_tree : Optional[EST[int]] = None
        self._node_radius = 11

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        if self.binary_tree is not None:
            '''
            drawing when a new point is added. Since the tree rotates this can change the entire
            layout and the full tree needs to be redrawn
            '''
            self._draw_tree(drawer, self.binary_tree.level_order(lambda n : Point(n.key, 0, 0)))

    def _draw_tree(self, drawer: Drawer, tree : list[list[Point]]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            cur_level = 0
            y_node = 0
            space_per_level = drawer.main_canvas.height / (len(tree) + 1)
            for level in tree:
                cur_node = 0
                y_node_parent = y_node
                y_node = drawer.main_canvas.height - (space_per_level * cur_level) - (space_per_level / 2)
                space_per_node = drawer.main_canvas.width / pow(2, cur_level)
                for node in level:
                    if node is not None:
                        x_node = space_per_node / 2 + (space_per_node * cur_node)
                        self._set_node_color(drawer, node.tag)
                        drawer.main_canvas.draw_string(int(x_node), int(y_node), str(int(node.x)))
                        drawer.main_canvas.draw_circle(Point(x_node, y_node), self._node_radius, self._line_width / 3)
                        if cur_level > 0:
                            # draw line between child and parent node
                            x_node_parent = space_per_node + (2 * space_per_node * math.floor(cur_node / 2))
                            p_self = Point(x_node, y_node)
                            p_parent = Point(x_node_parent, y_node_parent)
                            d = p_parent.distance(p_self)
                            d_norm = Point((x_node - x_node_parent) / d, (y_node - y_node_parent) / d)
                            drawer.main_canvas.draw_path(
                                [p_self - self._node_radius * d_norm, p_parent + self._node_radius * d_norm],
                                self._line_width)
                    cur_node += 1
                cur_level += 1
            drawer.main_canvas.set_colour(255,165,0)

    def _set_node_color(self, drawer : Drawer, tag : int):
        drawer.main_canvas.set_colour(COLOR_SCHEME[tag][0], COLOR_SCHEME[tag][1], COLOR_SCHEME[tag][2])

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        pass