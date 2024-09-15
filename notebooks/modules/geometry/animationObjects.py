'''
This file contains classes that are used as output by algorithms that need to be drawn (and animated).
The type variable 'O' is the output of an algorithm, eg.: an algorithm that returns a list of edges can return
an AnimationObject[list[edges]]
'''
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Iterator
from .core import Point

OUT = TypeVar("OUT")

# ---- ---- ---- ---- superclasses ---- ---- ---- ----

'''
Object to keep track of changes to data. See below for implementations
'''
class AnimationEvent(ABC, Generic[OUT]):
    @abstractmethod
    def execute_event(self, data : OUT):
        pass

'''
Output for all algorithms that get used in the visualisation tool
'''
class AnimationObject(ABC, Generic[OUT]):
    @abstractmethod
    def points(self) -> Iterator[Point]:
        pass

    def animation_events(self) -> Iterator[AnimationEvent]:
        return (PointAppendEvent(point) for point in self.points())

# ---- ---- ---- ---- Generic Implementations ---- ---- ---- ----

'''
if the used OUT class implements a pop method, it is called
'''
class PopEvent(AnimationEvent[OUT]):
    def execute_event(self, data : OUT):
        if callable(getattr(data, 'pop', None)):
            data.pop()

'''
if the used OUT class implements a clear method, it is called
'''
class ClearEvent(AnimationEvent[OUT]):
    def execute_event(self, data: OUT):
        if callable(getattr(data, 'clear', None)):
            data.clear()

# ---- ---- ---- ---- Implementation for Points ---- ---- ---- ----

class PointAppendEvent(AnimationEvent[list[Point]]):
    def __init__(self, point: Point):
        self.point = point

    def execute_on(self, points: list[Point]):
        points.append(self.point)

class PointSetEvent(AnimationEvent):
    def __init__(self, key: int, point: Point):
        self.key = key
        self.point = point

    def execute_on(self, points: list[Point]):
        points[self.key] = self.point

class PointDeleteEvent(AnimationEvent):
    def __init__(self, key: int):
        self.key = key

    def execute_on(self, points: list[Point]):
        del points[self.key]

class PointClearEvent(AnimationEvent):
    def execute_on(self, points: list[Point]):
        points.clear()
