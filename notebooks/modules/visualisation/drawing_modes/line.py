from __future__ import annotations
import time
from typing import Iterable

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    AnimationEvent,
    Point
)


class LineMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer:Drawer, points:Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        with drawer.main_canvas.hold():
            points_iter = iter(vertex_queue)
            cur_point = next(points_iter, None)
            while cur_point is not None:
                next_point = next(points_iter, None)
                if next_point is None:
                    drawer.main_canvas.draw_point(cur_point, transparent=True, radius=self._point_radius)
                else:
                    drawer.main_canvas.draw_line(cur_point, next_point, self._line_width)
                cur_point = next(points_iter, None)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        return NotImplemented