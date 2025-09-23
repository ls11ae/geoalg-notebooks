from ..drawing import DrawingMode, DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, Drawer
from typing import Iterable
from ...geometry import Point, AnimationEvent, PointList
from ...data_structures.animation_objects import StateChangedEvent
import time


class SmallestAreaTriangleMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        point_list = list(points)
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            vertices = [point for point in point_list if isinstance(point, PointList)]
            triangle = [point for point in point_list if not isinstance(point, PointList)]
            for point in vertices:
                drawer.main_canvas.draw_point(point, self._point_radius)
                for neighbor in point.data:
                    drawer.main_canvas.draw_path([point, neighbor], self._line_width)
            if triangle:
                drawer.main_canvas.set_colour(255,0,0)
                drawer.main_canvas.draw_path(triangle, self._line_width, close = True)
                drawer.main_canvas.set_colour(0,0,255)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        for point in points:
            # Draw point
            drawer.main_canvas.draw_point(point, self._point_radius)
            # Draw connections of the point
            if isinstance(point, PointList):
                for neighbor in point.data:
                    drawer.main_canvas.draw_path([point, neighbor], self._line_width)


    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        dcel: list[Point] = []
        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)
        while not isinstance(next_event, StateChangedEvent) and next_event is not None:
            next_event.execute_on(dcel)
            next_event = next(event_iterator, None)

        
        triangle = []
        drawer.main_canvas.set_colour(255,0,0)
        while next_event is not None:
            next_event.execute_on(triangle)

            with drawer.main_canvas.hold():
                drawer.main_canvas.clear()
                drawer.main_canvas.set_colour(0,0,255)
                self.draw(drawer,dcel)
                drawer.main_canvas.set_colour(255,0,0)
                self._draw_animation_step(drawer, triangle)
            
            next_event = next(event_iterator, None)
            time.sleep(animation_time_step)

        drawer.main_canvas.set_colour(0,0,255)
        self.draw(drawer,dcel + triangle)