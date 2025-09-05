from __future__ import annotations
import time
from typing import Iterable, Optional

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent, SetEvent,
    Point
)

class PathMode(DrawingMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._animation_path = []

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        path = []
        previous_vertex: Optional[Point] = drawer._get_drawing_mode_state()
        if previous_vertex is not None:
            path.append(previous_vertex)
        path.extend(points)
        if path:
            drawer._set_drawing_mode_state(path[-1])

        with drawer.main_canvas.hold():
            drawer.main_canvas.draw_points(path, self._vertex_radius)
            drawer.main_canvas.draw_path(path, self._line_width)

    def _draw_animation_step(self, drawer: Drawer):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            if self._animation_path:
                drawer.main_canvas.draw_points(self._animation_path[:-1], self._vertex_radius)
                drawer.main_canvas.draw_point(self._animation_path[-1], self._highlight_radius, transparent = True)
                drawer.main_canvas.draw_path(self._animation_path[:-1], self._line_width)
                drawer.main_canvas.draw_path(self._animation_path[-2:], self._line_width, transparent = True)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)

        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)

            if self._animation_path:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):
                    event = SetEvent(-1, next_event.point)
                if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                    if event.point == self._animation_path[-1]:
                        continue

            event.execute_on(self._animation_path)
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, self._animation_path)
        self._animation_path.clear()