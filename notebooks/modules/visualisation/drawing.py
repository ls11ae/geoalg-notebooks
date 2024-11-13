from __future__ import annotations
from abc import ABC, abstractmethod
from contextlib import contextmanager
from itertools import islice
import time
from typing import Any, Iterable, Iterator, Optional

from ..geometry import (
    AnimationEvent, AppendEvent, ClearEvent, PopEvent, SetEvent,
    Point, PointReference, PointList, LineSegment, Line, HorizontalOrientation as HORT, VerticalOrientation as VORT
)

from ipycanvas import Canvas, hold_canvas

DEFAULT_POINT_RADIUS = 5
DEFAULT_HIGHLIGHT_RADIUS = 12
DEFAULT_LINE_WIDTH = 3

class CanvasDrawingHandle:
    def __init__(self, canvas: Canvas):
        self._canvas = canvas
        self.set_colour(0, 0, 0)

    @contextmanager
    def hold(self):
        with hold_canvas(self._canvas):
            yield

    def set_colour(self, r: int, g: int, b: int):
        self.opaque_style = f"rgb({r}, {g}, {b})"
        self.transparent_style = f"rgba({r}, {g}, {b}, 0.25)"

        self._canvas.stroke_style = self.opaque_style
        self._canvas.fill_style = self.opaque_style

    def clear(self):
        self._canvas.clear()

    def draw_point(self, point: Point, radius: int, transparent: bool = False):
        if radius <= 0:
            return
        if transparent:
            self._canvas.fill_style = self.transparent_style
        self._canvas.fill_circle(point.x, point.y, radius)
        if transparent:
            self._canvas.fill_style = self.opaque_style

    def draw_points(self, points: Iterable[Point], radius: int, transparent: bool = False):
        if radius <= 0:
            return
        if transparent:
            self._canvas.fill_style = self.transparent_style
        for point in points:
            self._canvas.fill_circle(point.x, point.y, radius)
        if transparent:
            self._canvas.fill_style = self.opaque_style

    def draw_path(self, points: Iterable[Point], line_width: int, close: bool = False, stroke: bool = True,
    fill: bool = False, transparent: bool = False):
        points_iterator = iter(points)
        first_point = next(points_iterator, None)
        if first_point is None:
            return
        self._canvas.line_width = abs(line_width)

        self._canvas.begin_path()
        self._canvas.move_to(first_point.x, first_point.y)
        for point in points_iterator:
            self._canvas.line_to(point.x, point.y)
        
        if close:
            self._canvas.close_path()
        if transparent:
            self._canvas.stroke_style = self.transparent_style
            self._canvas.fill_style = self.transparent_style
        if stroke:
            self._canvas.stroke()
        if fill:
            self._canvas.fill(rule_or_path = "nonzero")
        if transparent:
            self._canvas.stroke_style = self.opaque_style
            self._canvas.fill_style  = self.opaque_style

    def draw_line(self, p1 : Point, p2 : Point, line_width:int, stroke:bool = True, transparent : bool = False):
        self._canvas.line_width = abs(line_width)
        line = Line(p1,p2)
        line.expand(Point(0,0), Point(self._canvas.width, self._canvas.height))
        '''
        seems to be a dirty fix:
        try and move p1 such that its x coord is 0, if this works also move p2 such that its endpoint is on the right canvas side
        if it doesnt work this means the line is parallel to the x axis, so try again by moving y coordinate around

        This is needed because the canvas cant draw a line crossing the whole screen unless the endpoints are on the border.
        So the only way is to move the endpoints
        '''
        self._canvas.begin_path()
        self._canvas.move_to(line.p1.x, line.p1.y)
        self._canvas.line_to(line.p2.x, line.p2.y)

        if transparent:
            self._canvas.stroke_style = self.transparent_style
            self._canvas.fill_style = self.transparent_style
        if stroke:
            self._canvas.stroke()
        if transparent:
            self._canvas.stroke_style = self.opaque_style
            self._canvas.fill_style  = self.opaque_style
        pass


    def draw_polygon(self, points: Iterable[Point], line_width: int, stroke: bool = True,
    fill: bool = False, transparent: bool = False):
        self.draw_path(points, line_width, close = True, stroke = stroke, fill = fill, transparent = transparent)

    @property
    def width(self) -> float:
        return self._canvas.width


class Drawer:
    def __init__(self, drawing_mode: DrawingMode, back_canvas: CanvasDrawingHandle,
    main_canvas: CanvasDrawingHandle, front_canvas: CanvasDrawingHandle):
        self._drawing_mode = drawing_mode
        self._drawing_mode_state = None
        self.back_canvas = back_canvas
        self.main_canvas = main_canvas
        self.front_canvas = front_canvas

    def _get_drawing_mode_state(self, default: Any = None) -> Any:    # TODO: This could be generic.
        if self._drawing_mode_state is None:
            self._drawing_mode_state = default
        return self._drawing_mode_state

    def _set_drawing_mode_state(self, state: Any):
        self._drawing_mode_state = state

    def clear(self):
        self._drawing_mode_state = None
        self.back_canvas.clear()
        self.main_canvas.clear()
        self.front_canvas.clear()

    def draw(self, points: Iterable[Point]):
        self._drawing_mode.draw(self, points)

    def animate(self, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        self.clear()
        self._drawing_mode.animate(self, animation_events, animation_time_step)


class DrawingMode(ABC):    # TODO: Maybe we can DRY this file after all...
    @abstractmethod
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        pass

    @abstractmethod
    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        pass


class PointsMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.draw_points(points, self._point_radius)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            if points:
                drawer.main_canvas.draw_points(points[:-1], self._point_radius)
                drawer.main_canvas.draw_point(points[-1], self._highlight_radius, transparent = True)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []

        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)
        i = 0
        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)
            if points:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):    # TODO: Maybe this can be done more elegantly.
                    event = SetEvent(-1, next_event.point)
                if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                    if event.point == points[-1]:
                        continue

            event.execute_on(points)
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, points)


class BoundingBoxMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width = DEFAULT_LINE_WIDTH):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
    
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        point_list = list(points)
        with drawer.main_canvas.hold():
            drawer.main_canvas.draw_polygon(point_list[0:4], self._line_width)

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
        for point in points:
                print(point)

class SweepLineMode(PointsMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH / 3):
        self._line_width = line_width
        super().__init__(point_radius, highlight_radius)
        
    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold(), drawer.front_canvas.hold():
            drawer.main_canvas.clear()
            drawer.front_canvas.clear()
            if points:
                drawer.main_canvas.draw_points(points[:-1], self._point_radius)
                drawer.main_canvas.draw_point(points[-1], self._highlight_radius, transparent = True)
                left_sweep_line_point = Point(0, points[-1].y)
                right_sweep_line_point = Point(drawer.front_canvas.width, points[-1].y)
                drawer.front_canvas.draw_path((left_sweep_line_point, right_sweep_line_point), self._line_width)


class ArtGalleryMode(PointsMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._line_width = line_width
        super().__init__(point_radius, highlight_radius)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        diagonal_points: list[Point] = []

        event_iterator = iter(animation_events)
        event = next(event_iterator, None)

        while event is not None and not isinstance(event, ClearEvent):
            event.execute_on(diagonal_points)
            event = next(event_iterator, None)

        with drawer.back_canvas.hold():
            for i in range(0, len(diagonal_points), 2):
                drawer.back_canvas.draw_path(diagonal_points[i:i + 2], self._line_width, transparent = True)

        super().animate(drawer, event_iterator, animation_time_step)


class PathMode(DrawingMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._animation_path = []

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        path = []
        previous_vertex: Optional[Point] = drawer._get_drawing_mode_state()
        if previous_vertex is not None:
            path.append(previous_vertex)
        path.extend(points)
        if path:
            drawer._set_drawing_mode_state(path[-1])

        with drawer.main_canvas.hold():
            drawer.main_canvas.draw_points(path, self._vertex_radius)
            drawer.main_canvas.draw_path(path, self._line_width)

    def _draw_animation_step(self, drawer: Drawer):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()
            if self._animation_path:
                drawer.main_canvas.draw_points(self._animation_path[:-1], self._vertex_radius)
                drawer.main_canvas.draw_point(self._animation_path[-1], self._highlight_radius, transparent = True)
                drawer.main_canvas.draw_path(self._animation_path[:-1], self._line_width)
                drawer.main_canvas.draw_path(self._animation_path[-2:], self._line_width, transparent = True)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)

        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)

            if self._animation_path:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):
                    event = SetEvent(-1, next_event.point)
                if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                    if event.point == self._animation_path[-1]:
                        continue

            event.execute_on(self._animation_path)
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, self._animation_path)
        self._animation_path.clear()


class PolygonMode(PathMode):           # TODO: If possible, maybe use composition instead of inheritance.
    def __init__(self, mark_closing_edge: bool, draw_interior: bool, vertex_radius: int = DEFAULT_POINT_RADIUS,
    highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(vertex_radius = vertex_radius, highlight_radius = highlight_radius, line_width = line_width)
        self._mark_closing_edge = mark_closing_edge
        self._draw_interior = draw_interior

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        polygon: list[Point] = drawer._get_drawing_mode_state(default = [])
        polygon.extend(points)

        drawer.main_canvas.clear()    # TODO: A clear is needed because the polygon can change. This is inconsistent with other modes.
        if self._draw_interior:
            drawer.back_canvas.clear()

        with drawer.main_canvas.hold(), drawer.back_canvas.hold():
            drawer.main_canvas.draw_points(polygon, self._vertex_radius)
            if self._mark_closing_edge and polygon:
                drawer.main_canvas.draw_path(polygon, self._line_width)
                drawer.main_canvas.draw_path((polygon[0], polygon[-1]), self._line_width, transparent = True)
            else:
                drawer.main_canvas.draw_polygon(polygon, self._line_width)
            if self._draw_interior:
                drawer.back_canvas.draw_polygon(polygon, self._line_width, stroke = False, fill = True, transparent = True)

    def _polygon_event_iterator(self, animation_events: Iterable[AnimationEvent]) -> Iterator[AnimationEvent]:
        yield from animation_events
        if self._animation_path:
            yield AppendEvent(self._animation_path[0])
            yield PopEvent()

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        super().animate(drawer, self._polygon_event_iterator(animation_events), animation_time_step)


class ChansHullMode(PolygonMode):
    @classmethod
    def from_polygon_mode(cls, polygon_mode: PolygonMode) -> ChansHullMode:
        return ChansHullMode(
            polygon_mode._mark_closing_edge,
            polygon_mode._draw_interior,
            vertex_radius = polygon_mode._vertex_radius,
            highlight_radius = polygon_mode._highlight_radius,
            line_width = polygon_mode._line_width
        )

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        container: Optional[list[Point]] = None

        event_iterator = self._polygon_event_iterator(animation_events)
        next_event = next(event_iterator, None)

        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)

            if self._animation_path:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):
                    event = SetEvent(-1, next_event.point)
                if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                    if event.point == self._animation_path[-1]:
                        continue
                    if isinstance(event.point, PointReference) and event.point.container is not container:
                        container = event.point.container
                        with drawer.front_canvas.hold():
                            drawer.front_canvas.clear()
                            drawer.front_canvas.draw_polygon(container, self._line_width / 3)
                        time.sleep(animation_time_step)

            event.execute_on(self._animation_path)
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, self._animation_path)
        self._animation_path.clear()


class FixedVertexNumberPathsMode(DrawingMode):
    def __init__(self, vertex_number: int, vertex_radius: int = DEFAULT_POINT_RADIUS,
    highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        if vertex_number < 1:
            raise ValueError("Vertex number needs to be positive.")
        self._vertex_number = vertex_number
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        initial_queue_length = len(vertex_queue)
        vertex_queue.extend(points)

        with drawer.main_canvas.hold():
            i, j = 0, self._vertex_number
            while j <= len(vertex_queue):
                path = vertex_queue[i:j]
                drawer.main_canvas.draw_points(path, self._vertex_radius)
                drawer.main_canvas.draw_path(path, self._line_width)
                i, j = j, j + self._vertex_number

            if i == 0:
                offset = int(initial_queue_length != 0)
                subpath = vertex_queue[initial_queue_length - offset:]
            else:
                offset = 0
                subpath = vertex_queue[i:]
                drawer._set_drawing_mode_state(subpath)
            drawer.main_canvas.draw_points(islice(subpath, offset, None), self._vertex_radius, transparent = True)
            drawer.main_canvas.draw_path(subpath, self._line_width, transparent = True)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold():
            drawer.main_canvas.clear()

            i, j = 0, self._vertex_number
            while j < len(points):
                path = points[i:j]
                drawer.main_canvas.draw_points(path, self._vertex_radius)
                drawer.main_canvas.draw_path(path, self._line_width)
                i, j = j, j + self._vertex_number

            path = points[i:]
            drawer.main_canvas.draw_points(path, self._highlight_radius, transparent = True)
            drawer.main_canvas.draw_path(path, self._line_width, transparent = True)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []

        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)

        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)

            if points:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):
                    event = SetEvent(-1, next_event.point)
                if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                    if event.point == points[-1] and len(points) % self._vertex_number != 0:
                        continue

            event.execute_on(points)
            if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                if isinstance(next_event, AppendEvent) or (isinstance(next_event, SetEvent) and next_event.key == -1):
                    if len(points) % self._vertex_number != 0:
                        continue
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, points)


class LineMode(DrawingMode):
    def __init__(self, point_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self.line_width = line_width

    def draw(self, drawer:Drawer, points:Iterable[Point]):
        vertex_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        vertex_queue.extend(points)
        with drawer.main_canvas.hold():
            points_iter = iter(vertex_queue)
            cur_point = next(points_iter, None)
            while cur_point is not None:
                next_point = next(points_iter, None)
                if(next_point is None):
                    drawer.main_canvas.draw_point(cur_point, transparent=True, radius=self._point_radius)
                else:
                    drawer.main_canvas.draw_line(cur_point, next_point, self.line_width)
                cur_point = next(points_iter, None)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        pass

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []
        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)
        while next_event is not None:
            next_event.execute_on(points)
            self._draw_animation_step(drawer, points)
            


class LineSegmentsMode(FixedVertexNumberPathsMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS,
    highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(2, vertex_radius, highlight_radius, line_width)


class MonotonePartitioningMode(DrawingMode):    # TODO: If possible, this could maybe make use of composition too.
    def __init__(self, animate_sweep_line: bool, vertex_radius: int = DEFAULT_POINT_RADIUS,
    highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._animate_sweep_line = animate_sweep_line
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        points: list[Point] = list(points)
        with drawer.main_canvas.hold():
            drawer.main_canvas.draw_points(points, self._vertex_radius)
            for i in range(0, len(points), 2):
                drawer.main_canvas.draw_path(points[i:i + 2], self._line_width)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold(), drawer.front_canvas.hold():
            drawer.main_canvas.clear()
            drawer.front_canvas.clear()

            if not points:
                return
            elif len(points) % 2 == 0:
                diagonal_points = points
                event_point = points[-2]
            else:
                diagonal_points = points[:-1]
                event_point = points[-1]

            drawer.main_canvas.draw_points(diagonal_points, self._vertex_radius)
            drawer.main_canvas.draw_point(event_point, self._highlight_radius, transparent = True)
            for i in range(0, len(diagonal_points), 2):
                drawer.main_canvas.draw_path(diagonal_points[i:i + 2], self._line_width)
            if self._animate_sweep_line:
                left_sweep_line_point = Point(0, event_point.y)
                right_sweep_line_point = Point(drawer.front_canvas.width, event_point.y)
                drawer.front_canvas.draw_path((left_sweep_line_point, right_sweep_line_point), self._line_width / 3)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        points: list[Point] = []

        event_iterator = iter(animation_events)
        next_event = next(event_iterator, None)

        while next_event is not None:
            event = next_event
            next_event = next(event_iterator, None)

            if points:
                if isinstance(event, PopEvent) and isinstance(next_event, AppendEvent):
                    event = SetEvent(-1, next_event.point)
                if isinstance(event, AppendEvent) or (isinstance(event, SetEvent) and event.key == -1):
                    if event.point == points[-1] and len(points) % 2 != 0:
                        continue

            event.execute_on(points)
            if len(points) >= 3 and len(points) % 2 == 1 and points[-1] == points[-3]:
                continue
            if isinstance(event, PopEvent) and next_event is None:
                break
            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, points)


class DCELMode(DrawingMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            for point in points:
                # Draw point
                drawer.main_canvas.draw_point(point, self._vertex_radius)
                # Draw connections of the point
                if isinstance(point, PointReference):
                    for i, neighbor in enumerate(point.container):
                        if i != point.position:
                            drawer.main_canvas.draw_path([point, neighbor], self._line_width)
                elif isinstance(point, PointList):
                    for neighbor in point.data:
                        drawer.main_canvas.draw_path([point, neighbor], self._line_width)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float): # TODO
        pass


class DCELModeUpdated(DrawingMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        point_queue: list[Point] = drawer._get_drawing_mode_state(default = [])
        with drawer.main_canvas.hold():
            for point in points:
                # Draw point
                if point not in point_queue:
                    drawer.main_canvas.draw_point(point, self._vertex_radius)
                # Draw connections of the point
                if not isinstance(point, PointReference):
                    continue
                for i, neighbor in enumerate(point.container):
                    if i != point.position:
                        drawer.main_canvas.draw_path([point, neighbor], self._line_width)
        point_queue.extend(points)  # Keep track of already drawn points

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float): # TODO
        pass

class VerticalExtensionMode(DrawingMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH,
                 animate_inserted_ls: bool = True):
        self._vertex_radius = vertex_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width
        self._animate_inserted_ls = animate_inserted_ls

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        with drawer.main_canvas.hold():
            for point in points:
                if not isinstance(point, PointReference) or len(point.container) == 1:
                    drawer.main_canvas.draw_point(point, self._vertex_radius)
                elif len(point.container) != 3 or point.position != 0:
                    raise Exception(f"Wrong format of the PointReference {point} for drawing vertical extensions.")
                else:
                    drawer.main_canvas.draw_point(point, self._vertex_radius)
                    drawer.main_canvas.draw_path([point.container[1], point.container[2]], self._line_width)

    def _draw_animation_step(self, drawer: Drawer, points: list[Point]):
        with drawer.main_canvas.hold(), drawer.front_canvas.hold():
            drawer.main_canvas.clear()
            drawer.front_canvas.clear()
            if not points:
                return
            else:
                drawer.front_canvas.draw_point(points[-1], self._highlight_radius, transparent = True)
            for point in points:
                if not isinstance(point, PointReference) or len(point.container) == 1:
                    drawer.front_canvas.draw_point(point, self._vertex_radius)
                elif len(point.container) == 2:
                    line_segment_list: list[Point] = drawer._get_drawing_mode_state(default = [])
                    line_segment_list.append(point.container)
                elif len(point.container) != 3 or point.position != 0:
                    raise Exception(f"Wrong format of the PointReference {point} for drawing vertical extensions.")
                else:
                    drawer.front_canvas.draw_point(point, self._vertex_radius)
                    drawer.front_canvas.draw_path([point.container[1], point.container[2]], self._line_width)
            line_segment_list = drawer._get_drawing_mode_state(default = [])
            if self._animate_inserted_ls:
                drawer.main_canvas.set_colour(0, 0, 0)  # black
                for line_segment in line_segment_list[:-1]:
                    drawer.main_canvas.draw_path(line_segment, self._line_width / 3)
                drawer.main_canvas.set_colour(0, 165, 0)  # green
            if len(line_segment_list) > 0:
                drawer.main_canvas.draw_path(drawer._get_drawing_mode_state(default = [])[-1], self._line_width)

    def animate(self, drawer: Drawer, animation_events: Iterable[AnimationEvent], animation_time_step: float):
        drawer.main_canvas.set_colour(0, 165, 0)  # green
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

            event.execute_on(points)

            if isinstance(event, PopEvent) and isinstance(next_event, SetEvent) \
                or isinstance(event, SetEvent) and event.key != -1 and isinstance(next_event, AppendEvent):
                continue

            if isinstance(event, PopEvent) and next_event is None:
                break

            self._draw_animation_step(drawer, points)
            time.sleep(animation_time_step)

        drawer.main_canvas.set_colour(0, 0, 255)  # blue
        drawer.front_canvas.set_colour(0, 0, 0)  # black
        drawer.clear()
        self.draw(drawer, points)


class PointLocationMode(PolygonMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS, highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(False, False, vertex_radius, highlight_radius, line_width)

    def draw(self, drawer: Drawer, points: Iterable[Point]):
        points = list(points)
        if len(points) > 1:
            super().draw(drawer, points[1:])  # Draw the path around the face containing the search point
        if len(points) > 0:
            drawer.front_canvas.set_colour(0, 165, 0)  # green
            drawer.front_canvas.draw_point(points[0], self._vertex_radius)  # Draw the search point (in green)
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
                    drawer.front_canvas.draw_point(point, self._vertex_radius)  # Draw the point of the x-node
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
                    drawer.front_canvas.draw_point(self._search_point, self._vertex_radius)
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