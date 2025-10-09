from ..drawing import DrawingMode, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, DEFAULT_POINT_RADIUS, Drawer
from ...geometry import Point, AnimationEvent, PointPair, PointList
import time
from typing import Iterable, cast
from ...data_structures import Triangulation

class TriangleMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
        self._draw_outer_points = True
    
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            for point in points:
                drawer.main_canvas.draw_point(point, self._line_width)
                if type(point) is PointList:
                    point = cast(PointList, point)
                    for edge_point in point.data:
                        drawer.main_canvas.draw_point(edge_point, self._line_width)
                        drawer.main_canvas.draw_path([point, edge_point], self._line_width)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            it = iter(points)
            cur = next(it, None)
            while cur is not None:
                if isinstance(cur, PointPair):
                    drawer.main_canvas.draw_path([cur, cur.data], self._line_width)
                else:
                    drawer.main_canvas.draw_point(cur, self._line_width)
                cur = next(it, None)