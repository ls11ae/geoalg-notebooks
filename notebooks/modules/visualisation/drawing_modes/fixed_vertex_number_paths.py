from __future__ import annotations
import time
from typing import Iterable
from itertools import islice

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent, SetEvent,
    Point
)


class FixedVertexNumberPathsMode(DrawingMode):
    def __init__(self, vertex_number: int, vertex_radius: int = DEFAULT_POINT_RADIUS,
    highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        if vertex_number < 1:
            raise ValueError("Vertex number needs to be positive.")
        self._vertex_number = vertex_number
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        initial_queue_length = len(vertex_queue)
        vertex_queue.extend(points)

        with drawer.main_canvas.hold():
            i, j = 0, self._vertex_number
            while j <= len(vertex_queue):
                path = vertex_queue[i:j]
                drawer.main_canvas.draw_points(path, self._vertex_radius)
                drawer.main_canvas.draw_path(path, self._line_width)
                i, j = j, j + self._vertex_number

            if i == 0:
                offset = int(initial_queue_length != 0)
                subpath = vertex_queue[initial_queue_length - offset:]
            else:
                offset = 0
                subpath = vertex_queue[i:]
                drawer._set_drawing_mode_state(subpath)
            drawer.main_canvas.draw_points(islice(subpath, offset, None), self._vertex_radius, transparent = True)
            drawer.main_canvas.draw_path(subpath, self._line_width, transparent = True)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()

            i, j = 0, self._vertex_number
            while j < len(points):
                path = points[i:j]
                drawer.main_canvas.draw_points(path, self._vertex_radius)
                drawer.main_canvas.draw_path(path, self._line_width)
                i, j = j, j + self._vertex_number

            path = points[i:]
            drawer.main_canvas.draw_points(path, self._highlight_radius, transparent = True)
            drawer.main_canvas.draw_path(path, self._line_width, transparent = True)

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
                    if event.point == points[-1] and len(points) % self._vertex_number != 0:
                        continue

            event.execute_on(points)
            if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                if isinstance(next_event, AppendEvent) or (isinstance(next_event, SetEvent) and next_event.key == -1):
                    if len(points) % self._vertex_number != 0:
                        continue
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, points)