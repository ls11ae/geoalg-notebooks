'''
Drawing modes that draw a point/line/linesegment and their respective dual. The ColorCycle is used to change color in every
step so objects that are duals of each other have the same color

The modes also offset the points and lines such that the origin of the canvas is moved to the center (assuming canvas is from 0 to 400).
This is needed to allow for visualisation of duality with negative coordinates.  
'''

from ..drawing import DrawingMode, DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, Drawer
from typing import Iterable
from time import time
from ...geometry import Point,Line, LineSegment, dual_point, dual_line, dual_lineSegment, AnimationEvent, PointList

X_OFFSET = 200
Y_OFFSET = 200
SCALE = 20

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

def offsetPoint(point : Point, invert : bool) -> Point:
    if invert:
        return Point((point.x * SCALE) + X_OFFSET, (point.y * SCALE) + Y_OFFSET)
    else:
        return Point((point.x - X_OFFSET)/SCALE, (point.y-Y_OFFSET)/SCALE)

def offsetLine(line : Line, invert : bool) -> Line:
    return Line(offsetPoint(line.p1, invert), offsetPoint(line.p2,invert))

def offsetLineSegment(lS: LineSegment, invert : bool) -> LineSegment:
    return LineSegment(offsetPoint(lS.lower,invert), offsetPoint(lS.upper,invert))

def offsetPoints(points : list[Point], invert : bool) -> list[Point]:
    return [offsetPoint(point,invert) for point in points]

def offsetLines(lines : list[Line], invert : bool) -> list[Line]:
    return [offsetLine(line,invert) for line in lines]

def offsetLineSegments(lSs : list[LineSegment], invert : bool) -> list[LineSegment]:
    return [offsetLineSegment(lS, invert) for lS in lSs]

class DualityPointsMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._color = ColorCycle(0,0,0,75)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        self._color.reset()
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            r,g,b = self._color.current()
            self._color.do_step()
            drawer.main_canvas.set_colour(r,g,b)
            #axis
            drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
            drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)
            for point in vertex_queue:
                r,g,b = self._color.current()
                self._color.do_step()
                drawer.main_canvas.set_colour(r,g,b)
                drawer.main_canvas.draw_point(point, self._point_radius)
                dual = offsetLine(dual_point(offsetPoint(point, False)), True)
                drawer.main_canvas.draw_line(dual.p1, dual.p2, line_width=self._line_width)  

    def animate(self, drawer, animation_events, animation_time_step):
        return super().animate(drawer, animation_events, animation_time_step)

class DualityLineMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._color = ColorCycle(0,0,0,75)
        
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
            #draw axis
            drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
            drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)
            while cur_point is not None:
                r,g,b = self._color.current()
                self._color.do_step()
                drawer.main_canvas.set_colour(r,g,b)
                next_point = next(points_iter, None)
                if(next_point is None):
                    drawer.main_canvas.draw_point(cur_point, transparent=True, radius=self._point_radius)
                else:
                    drawer.main_canvas.draw_line(cur_point, next_point, self._line_width)
                    drawer.main_canvas.draw_point(offsetPoint(dual_line(offsetLine(Line(cur_point, next_point),False)), True), self._point_radius)
                cur_point = next(points_iter, None)

    def animate(self, drawer, animation_events, animation_time_step):
        return super().animate(drawer, animation_events, animation_time_step)
        

class DualityLineSegmentMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH, draw_axis : bool = False):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._color = ColorCycle(0,0,0,75)

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
            #draw axis
            drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
            drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)
            while cur_point is not None:
                r,g,b = self._color.current()
                self._color.do_step()
                drawer.main_canvas.set_colour(r,g,b)
                next_point = next(points_iter, None)
                if(next_point is None):
                    drawer.main_canvas.draw_point(cur_point, transparent=True, radius=self._point_radius)
                else:
                    drawer.main_canvas.draw_path([cur_point, next_point], self._line_width)
                    duals = dual_lineSegment(offsetLineSegment(LineSegment(cur_point, next_point),False))
                    l1 = offsetLine(duals[0], True)
                    l2 = offsetLine(duals[1], True)
                    drawer.main_canvas.draw_line(l1.p1, l1.p2, self._line_width)
                    drawer.main_canvas.draw_line(l2.p1, l2.p2, self._line_width)
                cur_point = next(points_iter, None)
        
    def animate(self, drawer, animation_events, animation_time_step):
        return super().animate(drawer, animation_events, animation_time_step)
    

class SmallestAreaTriangleMode(DrawingMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        point_list = list(points)
        with drawer.main_canvas.hold():
            vertices = [point for point in point_list if isinstance(point, PointList)]
            triangle = [point for point in point_list if not isinstance(point, PointList)]
            for point in vertices:
                drawer.main_canvas.draw_point(point, self._vertex_radius)
                for neighbor in point.data:
                    drawer.main_canvas.draw_path([point, neighbor], self._line_width)
            drawer.main_canvas.set_colour(255,0,0)
            drawer.main_canvas.draw_path(triangle, self._line_width, close = True)
            drawer.main_canvas.set_colour(0,0,255)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            last : Point = None
            for point in points:
                # Draw point
                drawer.main_canvas.draw_point(point, self._vertex_radius)
                # Draw connections of the point
                if isinstance(point, PointList):
                    for neighbor in point.data:
                        drawer.main_canvas.draw_path([point, neighbor], self._line_width)
                elif isinstance(point, Point):
                    drawer.main_canvas.draw_point(point, self._line_width)
                    if(last is None):
                        last = point
                    else:
                        drawer.main_canvas.set_colour(255,0,0)
                        drawer.main_canvas.draw_path([last, point], self._line_width)
                        drawer.main_canvas.set_colour(0,0,255)
                        last = None


    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float): # TODO
        points: list[Point] = []
        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)
        while next_event is not None:
            next_event.execute_on(points)
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            self.draw(drawer,points)
