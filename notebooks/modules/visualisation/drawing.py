from __future__ import annotations

import time, math
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Iterable

from ..geometry import (
    AnimationEvent, 
    Point, Line
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

        #offset points of the line so they are out of the frame since the drawer only draws line segments
        offset_p1 : Point = None
        offset_p2 : Point = None
        try:
            offset_p1 = Point(0, line.y_from_x(0))
            offset_p2 = Point(self.width, line.y_from_x(self.width))
        except Exception:
            offset_p1 = Point(line.x_from_y(0), 0)
            offset_p2 = Point(line.x_from_y(self.height), self.height)

        
        self._canvas.begin_path()
        self._canvas.move_to(offset_p1.x, offset_p1.y)
        self._canvas.line_to(offset_p2.x, offset_p2.y)

        if transparent:
            self._canvas.stroke_style = self.transparent_style
            self._canvas.fill_style = self.transparent_style
        if stroke:
            self._canvas.stroke()
        if transparent:
            self._canvas.stroke_style = self.opaque_style
            self._canvas.fill_style  = self.opaque_style

    def draw_circle(self, center : Point, radius : float, line_width: int, stroke: bool = True,
    fill: bool = False, transparent: bool = False):
        self._canvas.line_width = abs(line_width)
        self._canvas.begin_path()
        self._canvas.arc(center.x, center.y, radius, 0, 360)
        if transparent:
            self._canvas.stroke_style = self.transparent_style
            self._canvas.fill_style = self.transparent_style
        if stroke:
            self._canvas.stroke()
        if transparent:
            self._canvas.stroke_style = self.opaque_style
            self._canvas.fill_style  = self.opaque_style

    def draw_polygon(self, points: Iterable[Point], line_width: int, stroke: bool = True,
    fill: bool = False, transparent: bool = False):
        self.draw_path(points, line_width, close = True, stroke = stroke, fill = fill, transparent = transparent)

    def draw_string(self, x : int, y : int, text : str):
        self._canvas.text_align = "center"
        self._canvas.save()
        self._canvas.scale(1, -1)
        self._canvas.fill_text(text,x,-y)
        self._canvas.restore()


    @property
    def width(self) -> float:
        return self._canvas.width
    
    @property
    def height(self) -> float:
        return self._canvas.height


class Drawer:
    def __init__(self, drawing_mode: DrawingMode, back_canvas: CanvasDrawingHandle,
    main_canvas: CanvasDrawingHandle, front_canvas: CanvasDrawingHandle):
        self._drawing_mode = drawing_mode
        self._drawing_mode_state = None
        self.back_canvas = back_canvas
        self.main_canvas = main_canvas
        self.front_canvas = front_canvas

    def get_drawing_mode_state(self, default: Any = None) -> Any:    # TODO: This could be generic.
        if self._drawing_mode_state is None:
            self._drawing_mode_state = default
        return self._drawing_mode_state

    def set_drawing_mode_state(self, state: Any):
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

    def __init__(self, point_radius, highlight_radius, line_width):
        self._point_radius = point_radius
        self._highlight_radius = highlight_radius
        self._line_width = line_width

    @abstractmethod
    def draw(self, drawer: Drawer, points: Iterable[Point]):
        pass

    @abstractmethod
    def _draw_animation_step(self, drawer: Drawer, points: Iterable[Point]):
        pass

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