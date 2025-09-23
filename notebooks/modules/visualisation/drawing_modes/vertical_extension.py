from __future__ import annotations
import time
from typing import Iterable

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    DrawingMode, Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent, SetEvent,
    Point, PointReference
)

class VerticalExtensionMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH,
                 animate_inserted_ls: bool = True):
        super().__init__(point_radius, highlight_radius, line_width)
        self._animate_inserted_ls = animate_inserted_ls

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            for point in points:
                if not isinstance(point, PointReference) or len(point.container) == 1:
                    drawer.main_canvas.draw_point(point, self._point_radius)
                elif len(point.container) != 3 or point.position != 0:
                    raise Exception(f"Wrong format of the PointReference {point} for drawing vertical extensions.")
                else:
                    drawer.main_canvas.draw_point(point, self._point_radius)
                    drawer.main_canvas.draw_path([point.container[1], point.container[2]], self._line_width)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold(), drawer.front_canvas.hold():
            drawer.main_canvas.clear()
            drawer.front_canvas.clear()
            if not points:
                return
            else:
                drawer.front_canvas.draw_point(points[-1], self._highlight_radius, transparent = True)
            for point in points:
                if not isinstance(point, PointReference) or len(point.container) == 1:
                    drawer.front_canvas.draw_point(point, self._point_radius)
                elif len(point.container) == 2:
                    line_segment_list: list[Point] = drawer._get_drawing_mode_state(default = [])
                    line_segment_list.append(point.container)
                elif len(point.container) != 3 or point.position != 0:
                    raise Exception(f"Wrong format of the PointReference {point} for drawing vertical extensions.")
                else:
                    drawer.front_canvas.draw_point(point, self._point_radius)
                    drawer.front_canvas.draw_path([point.container[1], point.container[2]], self._line_width)
            line_segment_list = drawer._get_drawing_mode_state(default = [])
            if self._animate_inserted_ls:
                drawer.main_canvas.set_colour(0, 0, 0)  # black
                for line_segment in line_segment_list[:-1]:
                    drawer.main_canvas.draw_path(line_segment, self._line_width / 3)
                drawer.main_canvas.set_colour(0, 165, 0)  # green
            if len(line_segment_list) > 0:
                drawer.main_canvas.draw_path(drawer._get_drawing_mode_state(default = [])[-1], self._line_width)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        drawer.main_canvas.set_colour(0, 165, 0)  # green
        drawer.front_canvas.set_colour(0, 0, 255)  # blue

        points: list[Point] = []
        
        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)

        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)

            if points:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):
                    event = SetEvent(-1, next_event.point)
                    next_event = next(event_iterator, None)

            event.execute_on(points)

            if isinstance(event, PopEvent) and isinstance(next_event, SetEvent) \
                or isinstance(event, SetEvent) and event.key != -1 and isinstance(next_event, AppendEvent):
                continue

            if isinstance(event, PopEvent) and next_event is None:
                break

            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        drawer.main_canvas.set_colour(0, 0, 255)  # blue
        drawer.front_canvas.set_colour(0, 0, 0)  # black
        drawer.clear()
        self.draw(drawer, points)