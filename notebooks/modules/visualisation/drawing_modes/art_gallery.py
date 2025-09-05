from __future__ import annotations
from typing import Iterable

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH,
    Drawer
)
from ...geometry import (
    Point
)

from ...geometry import (
    AnimationEvent, ClearEvent, 
    Point
)

from .points import PointsMode


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