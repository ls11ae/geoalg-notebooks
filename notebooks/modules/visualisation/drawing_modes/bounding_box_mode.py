from ..drawing import DrawingMode, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, DEFAULT_POINT_RADIUS, Drawer
from ...geometry import Point, AnimationEvent, SetEvent
import time
from typing import Iterable

class BoundingBoxMode(DrawingMode):
    """
    Drawing Mode for the BoundingBoxAnimator.
    
    Methods
    -------
    draw(drawer, points)
        draws a rectangle out of the first four points in the list, draws all other points in red with the last one being bigger
    animate(drawer, animation_events, animation_time_step)
        handles animation events one by one
        does not wait between SetEvents, to make sure the corners of the bounding box update in one step
    """

    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
    
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        point_list = list(points)
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            l = len(point_list)
            if l < 4:
                return
            drawer.main_canvas.draw_polygon(point_list[0:4], self._line_width)
            if l > 4:
                drawer.main_canvas.set_colour(255,0,0)
                drawer.main_canvas.draw_points(point_list[4:l], self._point_radius / 2)
                drawer.main_canvas.set_colour(0,0,255) #TODO:this assumes the standard color is blue

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            l = len(points)
            if l < 4:
                return
            drawer.main_canvas.draw_polygon(points[0:4], self._line_width)
            if l > 4:
                drawer.main_canvas.set_colour(255,0,0)
                drawer.main_canvas.draw_points(points[4:l-1], self._point_radius / 2)
                drawer.main_canvas.draw_point(points[l-1], self._point_radius)
                drawer.main_canvas.set_colour(0,0,255) #TODO:this assumes the standard color is blue

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