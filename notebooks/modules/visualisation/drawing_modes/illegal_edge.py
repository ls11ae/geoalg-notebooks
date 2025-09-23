from ..drawing import DrawingMode, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, DEFAULT_POINT_RADIUS, Drawer
from ...geometry import Point, AnimationEvent, PointFloat, PointPair
import time
from typing import Iterable

class IllegalEdgeMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            iterator = iter(points)
            cur_point = next(iterator, None)
            while cur_point is not None:
                next_point = next(iterator, None)
                if next_point is not None:
                    drawer.main_canvas.draw_path([cur_point, next_point], self._line_width)
                else:
                    drawer.main_canvas.draw_point(cur_point, self._line_width)
                cur_point = next(iterator, None)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            iterator = iter(points)
            cur_point = next(iterator, None)
            while cur_point is not None:
                if isinstance(cur_point, PointFloat):
                    drawer.main_canvas.set_colour(255,0,0)
                    drawer.main_canvas.draw_circle(cur_point, cur_point.data, self._line_width)
                    drawer.main_canvas.set_colour(0,0,255)
                elif isinstance(cur_point, PointPair):
                    drawer.main_canvas.draw_path([cur_point, cur_point.data], self._line_width)
                elif isinstance(cur_point, Point):
                    drawer.main_canvas.draw_point(cur_point, self._point_radius)
                cur_point = next(iterator, None)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []
        event_iterator = iter(animation_events)
        cur_event = next(event_iterator, None)
        while cur_event is not None:
            cur_event.execute_on(points)
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)
            cur_event = next(event_iterator, None)