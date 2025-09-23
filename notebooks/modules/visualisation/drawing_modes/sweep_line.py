from __future__ import annotations

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    Drawer
)
from ...geometry import (
    Point
)

from .points import PointsMode

class SweepLineMode(PointsMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH / 3):
        super().__init__(point_radius, highlight_radius, line_width)
        
    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold(), drawer.front_canvas.hold():
            drawer.main_canvas.clear()
            drawer.front_canvas.clear()
            if points:
                drawer.main_canvas.draw_points(points[:-1], self._point_radius)
                drawer.main_canvas.draw_point(points[-1], self._highlight_radius, transparent = True)
                left_sweep_line_point = Point(0, points[-1].y)
                right_sweep_line_point = Point(drawer.front_canvas.width, points[-1].y)
                drawer.front_canvas.draw_path((left_sweep_line_point, right_sweep_line_point), self._line_width)