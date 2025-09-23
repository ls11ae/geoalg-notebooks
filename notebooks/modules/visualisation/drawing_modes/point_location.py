from __future__ import annotations
import time
from typing import Iterable

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent, SetEvent, ClearEvent,
    Point, PointReference, LineSegment, 
    HorizontalOrientation as HORT, VerticalOrientation as VORT
)

from .polygon import PolygonMode

class PointLocationMode(PolygonMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(False, False, point_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        points = list(points)
        if len(points) > 1:
            super().draw(drawer, points[1:])  # Draw the path around the face containing the search point
        if len(points) > 0:
            drawer.front_canvas.set_colour(0, 165, 0)  # green
            drawer.front_canvas.draw_point(points[0], self._point_radius)  # Draw the search point (in green)
            drawer.front_canvas.set_colour(0, 0, 0)  # black

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.back_canvas.hold(), drawer.main_canvas.hold(), drawer.front_canvas.hold():
            drawer.main_canvas.clear()
            if not points:
                drawer.front_canvas.clear()
                return
            else:
                drawer.main_canvas.draw_point(points[-1], self._highlight_radius, transparent = True)  # Mark the last point
            for point in points:
                if not isinstance(point, PointReference) or len(point.container) == 1:  # x-node or leaf
                    drawer.front_canvas.draw_point(point, self._point_radius)  # Draw the point of the x-node
                    if self._search_point.horizontal_orientation(point) == HORT.LEFT:  # Safe points for drawing of valid area
                        self._right_point = point
                    else:
                        self._left_point = point
                elif len(point.container) == 2:  # y-node
                    drawer.front_canvas.draw_path(point.container, self._line_width)  # Draw line segment of the y-node
                    ls = LineSegment(point.container[0], point.container[1])
                    if self._search_point.vertical_orientation(ls) == VORT.BELOW:
                        self._top_line_segment = ls
                    else:
                        self._bottom_line_segment = ls
                else:
                    raise Exception(f"Wrong format of the PointReference {point} for drawing point location animation.")
            if self._draw_area:  # Drawing the trapezoid representing the valid area
                drawer.back_canvas.clear()
                drawer.back_canvas.draw_polygon([Point(self._left_point.x, self._top_line_segment.y_from_x(self._left_point.x)),
                                                Point(self._right_point.x, self._top_line_segment.y_from_x(self._right_point.x)),
                                                Point(self._right_point.x, self._bottom_line_segment.y_from_x(self._right_point.x)),
                                                Point(self._left_point.x, self._bottom_line_segment.y_from_x(self._left_point.x))],
                                                self._line_width, stroke = False, fill = True, transparent = True)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        # Drawing parameters
        canvas_width, canvas_height = drawer.main_canvas._canvas.width, drawer.main_canvas._canvas.height
        self._left_point: Point = Point(0, canvas_height)
        self._right_point: Point = Point(canvas_width, canvas_height)
        self._top_line_segment: LineSegment = LineSegment(self._left_point, self._right_point)
        self._bottom_line_segment: LineSegment = LineSegment(Point(0, 0), Point(canvas_width, 0))
        self._search_point: Point = None
        self._draw_area = True
        # Drawing colors
        drawer.back_canvas.set_colour(100, 100, 100)  # grey
        drawer.front_canvas.set_colour(0, 0, 255)  # blue
        
        points: list[Point] = []
        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)
        
        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)
            if points:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):
                    event = SetEvent(-1, next_event.point)
                    next_event = next(event_iterator, None)
            else:
                if isinstance(event, AppendEvent) and self._search_point is None:
                    self._search_point = event.point
                    # Mark the search point in green
                    drawer.front_canvas.set_colour(0, 165, 0)  # green
                    drawer.front_canvas.draw_point(self._search_point, self._point_radius)
                    drawer.front_canvas.set_colour(0, 0, 255)  # blue
                    continue
            
            event.execute_on(points)

            if isinstance(event, ClearEvent):
                self._draw_area = False
                while next_event is not None:  # Skip to the end after the search animation is finished
                    event = next_event
                    next_event = next(event_iterator, None)
                    event.execute_on(points)
                break

            if isinstance(event, PopEvent) and isinstance(next_event, SetEvent) \
                or isinstance(event, SetEvent) and event.key != -1 and isinstance(next_event, AppendEvent):
                continue

            if isinstance(event, PopEvent) and next_event is None:
                break

            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        # Reset colors
        drawer.back_canvas.set_colour(0, 0, 255)
        drawer.front_canvas.set_colour(0, 0, 0)
        # Final drawing
        drawer.clear()
        self.draw(drawer, points)