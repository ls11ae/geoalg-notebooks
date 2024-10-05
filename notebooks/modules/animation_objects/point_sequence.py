from __future__ import annotations
from .base import AnimationEvent, AnimationObject, AppendEvent, PopEvent, ClearEvent, SetEvent, DeleteEvent
from ..geometry import Point
from typing import Iterator, Iterable, Optional, Any, Union

class PointAnimation(AnimationObject):
    def __init__(self, points: Iterable[Point] = []):
        self._points: list[Point] = []
        self._animation_events: list[AnimationEvent] = []
        for point in points:
            self.append(point)

    def points(self) -> Iterator[Point]:
        return iter(self._points)

    def append(self, point: Point):
        self._points.append(point)
        self._animation_events.append(AppendEvent(point))

    def pop(self) -> Point:
        point = self._points.pop()
        self._animation_events.append(PopEvent())
        return point

    def update(self, old : Point, new : Point):
        i = self._points.index(old)
        self._points.remove(old)
        self._points.insert(i, new)
        self._animation_events.append(SetEvent(i, new))

    def delete(self, point : Point):
        self._animation_events.append(DeleteEvent(self._points.index(point)))
        self._points.remove(point)

    def clear(self):
        self._points.clear()
        self._animation_events.append(ClearEvent())

    def animate(self, point: Point):
        self._animation_events.append(AppendEvent(point))
        self._animation_events.append(PopEvent())

    def reset_animations(self):
        self._animation_events = list(super().animation_events())

    def _find(self, point: Point) -> Optional[Point]:
        for i, seq_point in enumerate(self._points):
            if point == seq_point:
                return i
        return None

    def __repr__(self) -> str:
        return self._points.__repr__()

    def __add__(self, other: Any) -> PointAnimation:
        if not isinstance(other, PointAnimation):
            raise TypeError("Parameter 'other' needs to be of type 'PointAnimation'.")
        result = PointAnimation()
        result._points = self._points + other._points
        result._animation_events = self._animation_events + other._animation_events
        return result

    def __len__(self) -> int:
        return len(self._points)

    def __getitem__(self, key: Any) -> Union[Point, PointAnimation]:
        if isinstance(key, Point):
            key = self._find(key)
            if key is None:
                return None
        if isinstance(key, int):
            return self._points[key]
        elif isinstance(key, slice) and (key.step is None or key.step == 1):
            # This implementation is a hack, but it works for Graham Scan.
            result = PointAnimation()
            result._points = self._points[key]
            result._animation_events = self._animation_events[:]
            return result
        else:
            raise ValueError("Parameter 'key' needs to be an integer or a slice with step 1.")

    def __setitem__(self, key: Any, new_point: Point):
        if isinstance(key, Point):
            key = self._find(key)
            if key is None:
                return
        elif not isinstance(key, int):
            raise ValueError("Parameter 'key' needs to be an integer or a point")
        self._points[key] = new_point
        self._animation_events.append(SetEvent(key, new_point))

    def __delitem__(self, key: Any):
        if not isinstance(key, int):
            raise ValueError("Parameter 'key' needs to be an integer.")
        del self._points[key]
        self._animation_events.append(DeleteEvent(key))