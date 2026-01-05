from __future__ import annotations
import time
from typing import Iterable, Optional
import math
from ...data_structures.binary_trees.base import BinaryTree

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    Point
)





class BinaryTreeMode(DrawingMode):
    """
    this is a very ugly fix but there just isn't another way :(
    """
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
        self.binary_tree : Optional[BinaryTree[Point]] = None
        self._node_radius = 11

    def draw(self, drawer: Drawer, points: Iterable[Point]):


        if self.binary_tree is None:
            '''
            drawing when the range search algorithm is used.
            The drawing mode for the algorithm has no binary_tree and instead draws
            '''
            pass
        else:
            '''
            drawing when a new point is added. Since the three rotates this can change the entire
            layout and the full tree need to be redrawn
            '''
            binary_tree = self.binary_tree.level_order()
            with drawer.main_canvas.hold():
                cur_level = 0
                y_node = 0
                space_per_level = drawer.main_canvas.height / (self.binary_tree.height + 1)
                for level in binary_tree:
                    cur_node = 0
                    y_node_parent = y_node
                    y_node = drawer.main_canvas.height - (space_per_level * cur_level) - (space_per_level / 2)
                    space_per_node = drawer.main_canvas.width / pow(2, cur_level)
                    for node in level:
                        if node is not None:
                            x_node = space_per_node/2 + (space_per_node * cur_node)
                            drawer.main_canvas.draw_string(int(x_node), int(y_node), str(int(node.x)))
                            drawer.main_canvas.draw_circle(Point(x_node,y_node), self._node_radius, self._line_width/3)
                            if cur_level > 0:
                                # draw line between child and parent node
                                x_node_parent = space_per_node + (2 * space_per_node* math.floor(cur_node/2))
                                p_self =  Point(x_node, y_node)
                                p_parent = Point(x_node_parent, y_node_parent)
                                d = p_parent.distance(p_self)
                                d_norm = Point((x_node - x_node_parent) / d, (y_node - y_node_parent) / d)
                                drawer.main_canvas.draw_path([p_self - self._node_radius * d_norm, p_parent + self._node_radius * d_norm], self._line_width)
                        cur_node += 1
                    cur_level += 1


    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        pass


"""


"""