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

class PointsMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.draw_points(points, self._point_radius)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            if points:
                drawer.main_canvas.draw_points(points[:-1], self._point_radius)
                drawer.main_canvas.draw_point(points[-1], self._highlight_radius, transparent = True)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []

        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)
        i = 0
        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)
            if points:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):    # TODO: Maybe this can be done more elegantly.
                    #merge popevent and appendevent to setevent
                    event = SetEvent(-1, next_event.point)
                if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                    #set event with key == -1 is just an appendEvent
                    #skip appendEvent if the point is already at the end of the list
                    if event.point == points[-1]:
                        continue

            event.execute_on(points)
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, points)