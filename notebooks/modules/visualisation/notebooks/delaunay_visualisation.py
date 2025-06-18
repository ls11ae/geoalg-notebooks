from ..drawing import DrawingMode, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, DEFAULT_POINT_RADIUS, Drawer
from ..instances import InstanceHandle
from ...geometry import Point, AnimationEvent, SetEvent, PointFloat, PointPair, AppendEvent, PopEvent
import time
from typing import Iterable, Optional
import numpy as np
from ...data_structures import Triangulation, P0, P1, P2

class TriangleInstance(InstanceHandle[Triangulation]):
    def __init__(self, p0 : Point = P0, p1 : Point = P1, p2 : Point = P2):
        self._p0 = p0
        self._p1 = p1
        self._p2 = p2
        self._drawing_mode = TriangleMode()
        self._instance : Triangulation = Triangulation(p0,p1,p2)
        self._drawing_mode.set_instance(self._instance)
        super().__init__(self._instance, self._drawing_mode, 10)
        
    def add_point(self, point: Point) -> bool:
        return self._instance.insert_point(point) is not None

    def clear(self):
        self._instance.reset(self._p0, self._p1, self._p2)

    def size(self) -> int:
        if self._instance is None:
            return 0
        return len(self._instance.edges_as_points()) / 2

    @staticmethod
    def extract_points_from_raw_instance(instance: Triangulation) -> list[Point]:
        if instance is None:
            return []
        return instance.edges_as_points()

    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        x_values = np.clip(np.random.normal(0.5 * max_x, 0.15 * max_x, number), 0.05 * max_x, 0.95 * max_x)
        y_values = np.clip(np.random.normal(0.5 * max_y, 0.15 * max_y, number), 0.05 * max_y, 0.95 * max_y)
        return [Point(x, y) for x, y in zip(x_values, y_values)]

class TriangleMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._instance = None

    def set_instance(self, triangulation : Triangulation):
        self._instance = triangulation
    
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        if self._instance is None:
            return
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            edges = iter(self._instance.edges_as_points())
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
            if(len(points) >= 4):
                drawer.main_canvas.draw_polygon(points[0:4], self._line_width)
                drawer.main_canvas.draw_points(points[4:], self._point_radius)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []
        event_iterator = iter(animation_events)
        event = next(event_iterator, None)
        while event is not None:
            event = next(event_iterator, None)            
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)
        self.draw(drawer, points)

class IllegalEdgeMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width

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
                    drawer.main_canvas.draw_circle(cur_point, cur_point.data, self._line_width)
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