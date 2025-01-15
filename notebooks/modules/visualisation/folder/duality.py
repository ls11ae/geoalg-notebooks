from ..drawing import DrawingMode, DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, Drawer
from typing import Iterable
from ...geometry import Point, AppendEvent, PopEvent, SetEvent, AnimationEvent
from time import time

class ColorCycle:
    def __init__(self, r : int, g : int, b : int, step : int):
        self._r = r
        self._g = g
        self._b = b
        self._step = step

    def current(self) -> tuple[int,int,int]:
        return (self._r,self._g,self._b)

    def do_step(self):
        self._r += self._step
        if(self._r > 255):
            self._r = 0
            self._g +=self._step
            if(self._g > 255):
                self._g = 0
                self._b += self._step
                if(self._b > 255):
                    self._b = 0

    def reset(self):
        self._r = 0
        self._g = 0
        self._b = 0

    @property
    def r(self) -> int:
        return self._r
    
    @r.setter
    def r(self, r):
        self._r = r
    
    @property
    def g(self) -> int:
        return self._g
    
    @r.setter
    def g(self, g):
        self._g = g
    
    @property
    def b(self) -> int:
        return self._b
    
    @b.setter
    def b(self, b):
        self._b = b
    
    @property
    def step(self) -> int:
        return self._step
    
    @step.setter
    def step(self, step):
        self._step = step

class DualityPointsMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH, draw_axis : bool = False):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._color = ColorCycle(0,0,0,75)
        self._draw_axis = draw_axis

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        self._color.reset()
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            r,g,b = self._color.current()
            self._color.do_step()
            drawer.main_canvas.set_colour(r,g,b)
            if self._draw_axis:
                self.draw_axis(drawer)
            for point in vertex_queue:
                r,g,b = self._color.current()
                self._color.do_step()
                drawer.main_canvas.set_colour(r,g,b)
                drawer.main_canvas.draw_point(point, self._point_radius)            

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points = []
        for event in animation_events:
            event.execute_on(points)
        self.draw(drawer,points)

    def draw_axis(self, drawer):
        drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
        drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)


class DualityLineMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH, draw_axis : bool = False, in_segments : bool = False):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._color = ColorCycle(0,0,0,75)
        self._draw_axis = draw_axis
        self._in_segments = in_segments
        

    def draw(self, drawer:Drawer, points:Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        self._color.reset()
        with drawer.main_canvas.hold():
            points_iter = iter(vertex_queue)
            cur_point = next(points_iter, None)
            r,g,b = self._color.current()
            drawer.main_canvas.set_colour(r,g,b)
            self._color.do_step()
            if(self._draw_axis):
                self.draw_axis(drawer)
            did_swap = False
            while cur_point is not None:
                if self._in_segments:
                    if not did_swap:
                        r,g,b = self._color.current()
                        self._color.do_step()
                        drawer.main_canvas.set_colour(r,g,b)
                        did_swap = not did_swap
                    else:
                        did_swap = not did_swap
                else:
                    r,g,b = self._color.current()
                    self._color.do_step()
                    drawer.main_canvas.set_colour(r,g,b)
                next_point = next(points_iter, None)
                if(next_point is None):
                    drawer.main_canvas.draw_point(cur_point, transparent=True, radius=self._point_radius)
                else:
                    drawer.main_canvas.draw_line(cur_point, next_point, self._line_width)
                cur_point = next(points_iter, None)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points = []
        for event in animation_events:
            event.execute_on(points)
        self.draw(drawer,points)

    def draw_axis(self, drawer):
        drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
        drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)

class DualityLineSegmentMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH, draw_axis : bool = False):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._color = ColorCycle(0,0,0,75)
        self._draw_axis = draw_axis

    def draw(self, drawer:Drawer, points:Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        self._color.reset()
        with drawer.main_canvas.hold():
            points_iter = iter(vertex_queue)
            cur_point = next(points_iter, None)
            r,g,b = self._color.current()
            self._color.do_step()
            drawer.main_canvas.set_colour(r,g,b)
            if(self._draw_axis):
                self.draw_axis(drawer)
            while cur_point is not None:
                r,g,b = self._color.current()
                self._color.do_step()
                drawer.main_canvas.set_colour(r,g,b)
                next_point = next(points_iter, None)
                if(next_point is None):
                    drawer.main_canvas.draw_point(cur_point, transparent=True, radius=self._point_radius)
                else:
                    drawer.main_canvas.draw_path([cur_point, next_point], self._line_width)
                cur_point = next(points_iter, None)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points = []
        for event in animation_events:
            event.execute_on(points)
        self.draw(drawer,points)

    def draw_axis(self, drawer):
        drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
        drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)