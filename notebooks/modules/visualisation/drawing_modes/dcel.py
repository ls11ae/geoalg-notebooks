from __future__ import annotations
import time
from typing import Iterable

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent,
    Point, PointReference, PointList, PointPair
)

#TODO: this should probably be unified to either use pointreference or pointlist instead of both
class DCELMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            for point in points:
                # Draw point
                drawer.main_canvas.draw_point(point, self._point_radius)
                # Draw connections of the point
                if isinstance(point, PointReference):
                    for i, neighbor in enumerate(point.container):
                        if i != point.position:
                            drawer.main_canvas.draw_path([point, neighbor], self._line_width)
                elif isinstance(point, PointList):
                    for neighbor in point.data:
                        drawer.main_canvas.draw_path([point, neighbor], self._line_width)
                else:
                    drawer.main_canvas.set_colour(255,0,0)
                    drawer.main_canvas.draw_point(point, self._point_radius)
                    drawer.main_canvas.set_colour(0,0,255)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            for point in points:
                # Draw connections of the point
                if isinstance(point, PointReference):
                    drawer.main_canvas.draw_point(point, self._point_radius)
                    for i, neighbor in enumerate(point.container):
                        if i != point.position:
                            drawer.main_canvas.draw_path([point, neighbor], self._line_width)
                #part used by arrangements
                elif isinstance(point, PointList):
                    drawer.main_canvas.draw_point(point, self._point_radius)
                    for neighbor in point.data:
                        drawer.main_canvas.draw_path([point, neighbor], self._line_width)
                elif isinstance(point, PointPair):
                    if point.tag == 0:
                        drawer.main_canvas.draw_line(point, point.data, self._highlight_radius, True, True)
                    if point.tag == 1:
                        drawer.main_canvas.set_colour(255, 0, 0)
                        drawer.main_canvas.draw_path([point, point.data], self._line_width)
                        drawer.main_canvas.set_colour(0, 0, 255)
                elif isinstance(point, Point):
                    drawer.main_canvas.draw_point(point, self._point_radius)