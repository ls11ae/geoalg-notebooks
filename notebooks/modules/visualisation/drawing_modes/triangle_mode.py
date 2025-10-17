from ..drawing import DrawingMode, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH, DEFAULT_POINT_RADIUS, Drawer
from ...geometry import Point, PointPair, PointList
from typing import Iterable

class TriangleMode(DrawingMode):
    def __init__(self, p0 : Point, p1: Point, p2: Point, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        super().__init__(point_radius, highlight_radius, line_width)
        self._outer_points = [p0,p1,p2]
        self._outer_triangle_drawn = False
    
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            if not self._outer_triangle_drawn:
                drawer.main_canvas.draw_point(self._outer_points[0], self._line_width)
                drawer.main_canvas.draw_point(self._outer_points[1], self._line_width)
                drawer.main_canvas.draw_point(self._outer_points[2], self._line_width)
                drawer.main_canvas.draw_path([self._outer_points[0], self._outer_points[1]], self._line_width)
                drawer.main_canvas.draw_path([self._outer_points[1], self._outer_points[2]], self._line_width)
                drawer.main_canvas.draw_path([self._outer_points[2], self._outer_points[0]], self._line_width)
                self._outer_triangle_drawn = True
            for point in points:
                if isinstance(point, PointList):
                    if point.tag > 3:
                        drawer.main_canvas.draw_point(point, self._line_width)

                    for connected_point in point.data:
                        if point.tag == 0 and connected_point.tag == 0:
                            drawer.main_canvas.draw_path([point, connected_point], self._line_width)
                        elif point.tag == 1 or connected_point.tag == 1:
                            drawer.main_canvas.draw_path([point, connected_point], self._line_width, transparent=True)
                        #voronoi
                        elif point.tag == 2 and connected_point.tag == 2:
                            drawer.main_canvas.set_colour(255, 165, 0)
                            drawer.main_canvas.draw_path([point, connected_point], self._line_width, transparent=True)
                            drawer.main_canvas.set_colour(0, 0, 255)
                        elif point.tag > 3:
                            drawer.main_canvas.draw_path([point, connected_point], self._line_width)


    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            it = iter(points)
            cur = next(it, None)
            while cur is not None:
                if isinstance(cur, PointPair):
                    if cur._tag == 0:
                        drawer.main_canvas.draw_path([cur, cur.data], self._line_width)
                    if cur._tag == 1:
                        drawer.main_canvas.draw_path([cur, cur.data], self._line_width, transparent=True)
                else:
                    drawer.main_canvas.draw_point(cur, self._line_width)
                cur = next(it, None)

    @property
    def outer_triangle_drawn(self) -> bool:
        return self._outer_triangle_drawn

    @outer_triangle_drawn.setter
    def outer_triangle_drawn(self, value: bool):
        self._outer_triangle_drawn = value