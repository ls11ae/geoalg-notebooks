from __future__ import annotations
from typing import Iterable, Iterator

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent, 
    Point
)

from .path import PathMode

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