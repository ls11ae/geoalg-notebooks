from ..drawing import DrawingMode, DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, Drawer
from typing import Iterable
from ...geometry import Point, AnimationEvent, PointList, PointPair
import time


class SmallestAreaTriangleMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            for point in points:
                if isinstance(point, PointPair):
                    if point.tag == 0:
                        drawer.main_canvas.draw_line(point, point.data, self._highlight_radius, True, True)
                    elif point.tag == 1 or point.tag == 2:
                        drawer.main_canvas.set_colour(255, 0, 0)
                        drawer.main_canvas.draw_path([point, point.data], self._line_width, close=True)
                        drawer.main_canvas.set_colour(0, 0, 255)
                elif isinstance(point, PointList):
                    if point.tag == 1:
                        drawer.main_canvas.set_colour(255, 0, 0)
                    drawer.main_canvas.draw_point(point, self._point_radius)
                    for neighbor in point.data:
                        drawer.main_canvas.draw_path([point, neighbor], self._line_width)
                    drawer.main_canvas.set_colour(0, 0, 255)
                else:
                    if point.tag == 1:
                        drawer.main_canvas.set_colour(255, 0, 0)
                        drawer.main_canvas.draw_point(point, self._point_radius)
                        drawer.main_canvas.set_colour(0, 0, 255)
                    else:
                        drawer.main_canvas.draw_point(point, self._point_radius)


    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        self.draw(drawer,points)