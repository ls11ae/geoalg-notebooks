from ..drawing import DrawingMode, DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, Drawer
from typing import Iterable
from ...geometry import Point,Line, LineSegment, dual_point, dual_line, dual_lineSegment
from abc import abstractmethod

X_OFFSET = 200
Y_OFFSET = 200
SCALE = 20

'used to draw each object + dual pair in a different color so different pairs can be distinguished'
COLOR_SCHEME = [165,0,38], [215,48,39], [244,109,67], [253,174,97], [254,224,144], [171,217,233], [116,173,209], [69,117,180], [49,54,149]

# -------- offset methods --------

def offset_point(point : Point, invert : bool) -> Point:
    if invert:
        return Point((point.x * SCALE) + X_OFFSET, (point.y * SCALE) + Y_OFFSET)
    else:
        return Point((point.x - X_OFFSET)/SCALE, (point.y-Y_OFFSET)/SCALE)

def offset_line(line : Line, invert : bool) -> Line:
    return Line(offset_point(line.p1, invert), offset_point(line.p2, invert))

def offset_line_segment(line_segment: LineSegment, invert : bool) -> LineSegment:
    return LineSegment(offset_point(line_segment.lower, invert), offset_point(line_segment.upper, invert))

def offset_points(points : list[Point], invert : bool) -> list[Point]:
    return [offset_point(point, invert) for point in points]

def offset_lines(lines : list[Line], invert : bool) -> list[Line]:
    return [offset_line(line, invert) for line in lines]

def offset_line_segments(line_segments : list[LineSegment], invert : bool) -> list[LineSegment]:
    return [offset_line_segment(line_segments, invert) for line_segments in line_segments]

# -------- drawing modes --------

class DualityPointsMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        vertex_queue: list[Point] = drawer.get_drawing_mode_state(default = [])
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
                dual = offset_line(dual_point(offset_point(point, False)), True)
                drawer.main_canvas.draw_line(dual.p1, dual.p2, line_width=self._line_width)  

    def _draw_animation_step(self, drawer: Drawer, points: Iterable[Point]):
        return NotImplemented


class DualityMode(DrawingMode):
    """
    Superclass used to avoid duplicate code fragments from DualityLineMode and DualityLineSegmentMode.

    Methods
    -------
    hanlde_points(drawer, cur_point, next_point)
        overwritten by DualityLineMode and DualityLineSegmentMode to handle a pair of two points
    """

    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        vertex_queue: list[Point] = drawer.get_drawing_mode_state(default=[])
        vertex_queue.extend(points)
        with drawer.main_canvas.hold():
            # draw axis
            drawer.main_canvas.set_colour(0, 0, 0)
            drawer.main_canvas.draw_line(Point(200, 0), Point(200, 400), self._line_width / 2)
            drawer.main_canvas.draw_line(Point(0, 200), Point(400, 200), self._line_width / 2)
            points_iter = iter(vertex_queue)
            color_iter = iter(COLOR_SCHEME)
            cur_point = next(points_iter, None)
            cur_color = next(color_iter, None)
            while (cur_point is not None) and (cur_color is not None):
                drawer.main_canvas.set_colour(cur_color[0], cur_color[1], cur_color[2])
                cur_color = next(color_iter, None)
                next_point = next(points_iter, None)
                if next_point is None:
                    drawer.main_canvas.draw_point(cur_point, transparent=True, radius=self._point_radius)
                else:
                    self.handle_points(drawer, cur_point, next_point)
                cur_point = next(points_iter, None)


    @abstractmethod
    def handle_points(self, drawer: Drawer, cur_point: Point, next_point: Point):
        pass

    def _draw_animation_step(self, drawer: Drawer, points: Iterable[Point]):
        return NotImplemented


class DualityLineMode(DualityMode):

    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def handle_points(self, drawer: Drawer, cur_point: Point, next_point: Point):
        drawer.main_canvas.draw_line(cur_point, next_point, self._line_width)
        drawer.main_canvas.draw_point(offset_point(dual_line(offset_line(Line(cur_point, next_point), False)), True),
                                      self._point_radius)
        

class DualityLineSegmentMode(DualityMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)

    def handle_points(self, drawer: Drawer, cur_point: Point, next_point: Point):
        drawer.main_canvas.draw_path([cur_point, next_point], self._line_width)
        duals = dual_lineSegment(offset_line_segment(LineSegment(cur_point, next_point), False))
        l1 = offset_line(duals[0], True)
        l2 = offset_line(duals[1], True)
        drawer.main_canvas.draw_line(l1.p1, l1.p2, self._line_width)
        drawer.main_canvas.draw_line(l2.p1, l2.p2, self._line_width)