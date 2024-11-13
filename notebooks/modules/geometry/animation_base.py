from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator
from .core import Point

# ---- ---- ---- ---- superclasses ---- ---- ---- ----

class AnimationObject(ABC):
    def __init__(self) -> None:
        super().__init__()
        self._animation_events: list[AnimationEvent] = []

    @abstractmethod
    def points(self) -> Iterator[Point]:
        pass

    def animation_events(self) -> Iterator[AnimationEvent]:
        return self._animation_events

'''
Object to keep track of changes to data. See below for implementations
'''
class AnimationEvent(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def execute_on(self, data : list[Point]):
        pass

class AppendEvent(AnimationEvent):
    def __init__(self, point: Point):
        self.point = point

    def execute_on(self, points: list[Point]):
        points.append(self.point)


class PopEvent(AnimationEvent):
    def execute_on(self, points: list[Point]):
        points.pop()


class SetEvent(AnimationEvent):
    def __init__(self, key: int, point: Point):
        self.key = key
        self.point = point

    def execute_on(self, points: list[Point]):
        points[self.key] = self.point


class MultiSetEvent(AnimationEvent):
    def __init__(self, keys : list[int], points : list[Point]):
        self._keys = keys
        self._points = points

    def execute_on(self, points:list[Point]):
        for i in range(0, min(len(self._keys), len(self._points))):
            points[self._keys[i]] = self._points[i]


class DeleteAtEvent(AnimationEvent):
    def __init__(self, key: int):
        self.key = key

    def execute_on(self, points: list[Point]):
        del points[self.key]

class  UpdateEvent(AnimationEvent):
    def __init__(self, old : Point, new : Point):
        self._old = old
        self._new = new
    
    def execute_on(self, points:list[Point]):
        i = points.index(self._old)
        points.remove(self._old)
        points.insert(i, self._new)

class UpdateXEvent(AnimationEvent):
    def __init__(self, points : list[Point]):
        self._points = points
    
    def execute_on(self, points : list[Point]):
        for i in range(0, min(len(self._points), len(points))):
            points[i] = self._points[i]

class  DeleteEvent(AnimationEvent):
    def __init__(self, to_del : Point):
        self._to_del = to_del
    
    def execute_on(self, points:list[Point]):
        points.remove(self._to_del)

class ClearEvent(AnimationEvent):
    def execute_on(self, points: list[Point]):
        points.clear()