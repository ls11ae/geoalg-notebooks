from __future__ import annotations
import time
from typing import Iterable, Optional
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

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        if self.binary_tree is None:
            return
        binary_tree = self.binary_tree.level_order()
        with drawer.main_canvas.hold():
            cur_level = 0
            space_per_level = drawer.main_canvas.height / self.binary_tree.height
            drawer.main_canvas.draw_string(int(0), int(100), str(self.binary_tree.height))
            space_per_node = drawer.main_canvas.width / pow(2, cur_level)
            for level in binary_tree:
                cur_node = 0
                y = drawer.main_canvas.height - (space_per_level * cur_level) - (space_per_level / 2)
                drawer.main_canvas.draw_string(int(200), int(y), str(space_per_node))
                for node in level:
                    x = space_per_node + (space_per_node * cur_node)
                    text = "" if node is None else int(node.x)
                    #drawer.main_canvas.draw_string(int(x), int(y), str(text))
                    cur_node += 1
                cur_level += 1
                space_per_node = drawer.main_canvas.width / pow(2, cur_level)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        pass


"""


"""