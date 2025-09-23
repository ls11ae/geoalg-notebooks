from __future__ import annotations
import time
from typing import Iterable

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent, SetEvent,
    Point
)


class MonotonePartitioningMode(DrawingMode):    # TODO: If possible, this could maybe make use of composition too.
    def __init__(self, animate_sweep_line: bool, point_radius: int = DEFAULT_POINT_RADIUS,
    highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
        self._animate_sweep_line = animate_sweep_line

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        points: list[Point] = list(points)
        with drawer.main_canvas.hold():
            drawer.main_canvas.draw_points(points, self._point_radius)
            for i in range(0, len(points), 2):
                drawer.main_canvas.draw_path(points[i:i + 2], self._line_width)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold(), drawer.front_canvas.hold():
            drawer.main_canvas.clear()
            drawer.front_canvas.clear()

            if not points:
                return
            elif len(points) % 2 == 0:
                diagonal_points = points
                event_point = points[-2]
            else:
                diagonal_points = points[:-1]
                event_point = points[-1]

            drawer.main_canvas.draw_points(diagonal_points, self._point_radius)
            drawer.main_canvas.draw_point(event_point, self._highlight_radius, transparent = True)
            for i in range(0, len(diagonal_points), 2):
                drawer.main_canvas.draw_path(diagonal_points[i:i + 2], self._line_width)
            if self._animate_sweep_line:
                left_sweep_line_point = Point(0, event_point.y)
                right_sweep_line_point = Point(drawer.front_canvas.width, event_point.y)
                drawer.front_canvas.draw_path((left_sweep_line_point, right_sweep_line_point), self._line_width / 3)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []

        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)

        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)

            if points:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):
                    event = SetEvent(-1, next_event.point)
                if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                    if event.point == points[-1] and len(points) % 2 != 0:
                        continue

            event.execute_on(points)
            if len(points) >= 3 and len(points) % 2 == 1 and points[-1] == points[-3]:
                continue
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, points)
