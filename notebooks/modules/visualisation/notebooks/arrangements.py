from ..drawing import DrawingMode, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, DEFAULT_POINT_RADIUS, Drawer
from ...geometry import Point, AnimationEvent, SetEvent
import time
from typing import Iterable

class BoundingBoxMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
    
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        point_list = list(points)
        with drawer.main_canvas.hold():
            drawer.main_canvas.draw_polygon(point_list[0:4], self._line_width)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            if(len(points) >= 4):
                drawer.main_canvas.draw_polygon(points[0:4], self._line_width)
                drawer.main_canvas.draw_points(points[4:], self._point_radius)


    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []
        event_iterator = iter(animation_events)
        event = next(event_iterator, None)
        while event is not None:
            if(type(event) is SetEvent):
                while type(event) is SetEvent:
                    event.execute_on(points)
                    event = next(event_iterator, None)
            else:
                event.execute_on(points)
                event = next(event_iterator, None)            
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)
        self.draw(drawer, points)