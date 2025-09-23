from ..drawing import DrawingMode, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, DEFAULT_POINT_RADIUS, Drawer
from ...geometry import Point, AnimationEvent, PointPair
import time
from typing import Iterable
from ...data_structures import Triangulation

class TriangleMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
        self._instance = None
        self._draw_outer_points = True

    def set_instance(self, triangulation : Triangulation):
        self._instance = triangulation
    
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        if self._instance is None:
            return
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            edges = iter(self._instance.edges_as_points(self._draw_outer_points))
            cur = next(edges, None)
            while cur is not None:
                nex = next(edges, None)
                if nex is not None:
                    
                    drawer.main_canvas.draw_path([cur, nex], self._line_width)
                else:
                    drawer.main_canvas.draw_point(cur, self._line_width)
                cur = next(edges, None)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            it = iter(points)
            cur = next(it, None)
            while cur is not None:
                if isinstance(cur, PointPair):
                    drawer.main_canvas.draw_path([cur, cur.data], self._line_width)
                else:
                    drawer.main_canvas.draw_point(cur, self._line_width)
                cur = next(it, None)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []
        event_iterator = iter(animation_events)
        event = next(event_iterator, None)
        while event is not None:
            event.execute_on(points)           
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)
            event = next(event_iterator, None) 
        self.draw(drawer, points)