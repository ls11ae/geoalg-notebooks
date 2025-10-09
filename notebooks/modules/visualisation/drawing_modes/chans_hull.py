from __future__ import annotations
import time
from typing import Iterable, Optional

from ..drawing import (
    Drawer
)

from ...geometry import (
    AnimationEvent, AppendEvent, PopEvent, SetEvent,
    Point, PointReference
)

from .polygon import PolygonMode

class ChansHullMode(PolygonMode):
    @classmethod
    def from_polygon_mode(cls, polygon_mode: PolygonMode) -> ChansHullMode:
        return ChansHullMode(
            polygon_mode._mark_closing_edge,
            polygon_mode._draw_interior,
            point_radius = polygon_mode._point_radius,
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
            self._draw_animation_step(drawer, [])
            time.sleep(animation_time_step)

        drawer.clear()
        self.draw(drawer, self._animation_path)
        self._animation_path.clear()