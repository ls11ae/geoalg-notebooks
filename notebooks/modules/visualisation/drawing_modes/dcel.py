from __future__ import annotations
import time
from typing import Iterable

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent,
    Point, PointReference, PointList
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
            last : Point = None
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
                elif isinstance(point, Point) and point.tag < 4:
                    if(last is None):
                        last = point
                    else:
                        drawer.main_canvas.set_colour(255,0,0)
                        drawer.main_canvas.draw_path([last, point], self._line_width)
                        drawer.main_canvas.set_colour(0,0,255)
                        last = None


    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []
        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)
        while next_event is not None:
            next_event.execute_on(points)
            if type(next_event) is AppendEvent:
                next_event = next(event_iterator, None)
                while(type(next_event) is AppendEvent):
                    next_event.execute_on(points)
                    next_event = next(event_iterator, None)
            elif type(next_event) is PopEvent:
                next_event = next(event_iterator, None)
                while(type(next_event) is PopEvent):
                    next_event.execute_on(points)
                    next_event = next(event_iterator, None)
            else:
                next_event = next(event_iterator, None)
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            self.draw(drawer,points)