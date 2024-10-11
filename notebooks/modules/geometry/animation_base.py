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


class DeleteEvent(AnimationEvent):
    def __init__(self, key: int):
        self.key = key

    def execute_on(self, points: list[Point]):
        del points[self.key]


class ClearEvent(AnimationEvent):
    def execute_on(self, points: list[Point]):
        points.clear()