from ..drawing import DrawingMode, DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, Drawer
from typing import Iterable
from ...geometry import Point,Line, LineSegment, dual_point, dual_line, dual_lineSegment

X_OFFSET = 200
Y_OFFSET = 200
SCALE = 20

COLOR_SCHEME = [165,0,38], [215,48,39], [244,109,67], [253,174,97], [254,224,144], [171,217,233], [116,173,209], [69,117,180], [49,54,149]

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

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        with drawer.main_canvas.hold():
            #draw axis in black
            drawer.main_canvas.clear()
            drawer.main_canvas.set_colour(0,0,0)
            drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
            drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)
            #draw points
            for point, color in zip(vertex_queue, COLOR_SCHEME):
                drawer.main_canvas.set_colour(color[0], color[1], color[2])
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
        
    def draw(self, drawer:Drawer, points:Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        with drawer.main_canvas.hold():
            
            #draw axis
            drawer.main_canvas.set_colour(0,0,0)
            drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
            drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)
            points_iter = iter(vertex_queue)
            color_iter = iter(COLOR_SCHEME)
            cur_point = next(points_iter, None)
            cur_color = next(color_iter, None)
            while (cur_point is not None) and (cur_color is not None):
                drawer.main_canvas.set_colour(cur_color[0], cur_color[1], cur_color[2])
                cur_color = next(color_iter, None)
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

    def draw(self, drawer:Drawer, points:Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        with drawer.main_canvas.hold():
            
            #draw axis
            drawer.main_canvas.set_colour(0,0,0)
            drawer.main_canvas.draw_line(Point(200,0), Point(200,400), self._line_width/2)
            drawer.main_canvas.draw_line(Point(0,200), Point(400,200), self._line_width/2)
            points_iter = iter(vertex_queue)
            color_iter = iter(COLOR_SCHEME)
            cur_point = next(points_iter, None)
            cur_color = next(color_iter, None)
            while (cur_point is not None) and (cur_color is not None):
                drawer.main_canvas.set_colour(cur_color[0], cur_color[1], cur_color[2])
                cur_color = next(color_iter, None)
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