from enum import Enum, auto
import math
import numpy as np

from typing import Callable, Iterable, Union

class Orientation(Enum):
    LEFT = auto()
    RIGHT = auto()
    BEHIND_SOURCE = auto()
    BETWEEN = auto()
    BEHIND_TARGET = auto()

class Point:
    def __init__(self,x,y):
        #self.x = x
        #self.y = y
        self.coords = np.array([x, y])

    @property
    def x(self):
        return self.coords[0]
    
    @property
    def y(self):
        return self.coords[1]
        
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))
    
    def __repr__(self):
        return f"Point({self.x}, {self.y})"
    
    def distance(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def orientation(self, source: 'Point', target: 'Point') -> Orientation:
        if source == target:
            raise ValueError("Line (segment) needs two different points")
        val = (target.x - source.x) * (self.y - source.y) - (target.y - source.y) * (self.x - source.x)
        if val > 0.0:
            return Orientation.LEFT
        elif val < 0.0:
            return Orientation.RIGHT
        else:
            if source.x != target.x:
                param = (self.x - source.x) / (target.x - source.x)
            else:
                param = (self.y - source.y) / (target.y - source.y)
            if param < 0.0:
                return Orientation.BEHIND_SOURCE
            elif param > 1.0:
                return Orientation.BEHIND_TARGET
            else:
                return Orientation.BETWEEN
            
class PointRef(Point):
    def __init__(self, container: list[Point], pos: int):
        self.container = container
        self.pos = pos
        
    def get_point(self) -> Point:
        return self.container[self.pos]
    
    @property
    def x(self):
        return self.get_point().x
    
    @property
    def y(self):
        return self.get_point().y

    def get_position(self):
        return self.pos
    
    def is_in_container(self, container: list[Point]) -> bool:
        return container is self.container


class AppendEvent:
    def __init__(self, point):
        self.point = point

    def execute_on(self, points: list[Point]):
        points.append(self.point)

class PopEvent:
    def execute_on(self, points: list[Point]):
        points.pop()

class SetEvent:
    def __init__(self, key, point):
        self.key = key
        self.point = point

    def execute_on(self, points: list[Point]):
        points[self.key] = self.point

class DeleteEvent:
    def __init__(self, key):
        self.key = key

    def execute_on(self, points: list[Point]):
        del points[self.key]

Event = Union[AppendEvent, PopEvent, SetEvent, DeleteEvent]


class Polygon:
    def __init__(self, points: Iterable[Point] = []):
        self.points: list[Point] = []
        self.events: list[Event] = []
        self.extend(points)

    def append(self, point: Point):
        self.points.append(point)

        if self.events and isinstance(self.events[-1], PopEvent):           # For GiftWrapping.
            self.events[-1] = SetEvent(-1, point)
        else:
            self.events.append(AppendEvent(point))      # can improve Graham here

    def extend(self, points: Iterable[Point]):
        for p in points:
            self.append(p)

    def pop(self) -> Point:
        point = self.points.pop()
        self.events.append(PopEvent())
        return point

    def __repr__(self) -> str:
        return self.points.__repr__()

    def __len__(self) -> int:
        return len(self.points)

    def __getitem__(self, key) -> Union[Point, 'Polygon']:
        # This implementation is a hack, but it works for Graham Scan. (Though not perfectly...)
        if isinstance(key, slice):
            if key.step is not None and key.step != 1:
                raise ValueError("Polyline doesn't accept slice keys with a step different from 1.")
            result = Polygon()
            result.points = self.points[key]
            result.events = self.events[:]
            return result
        return self.points[key]

    def __delitem__(self, key):
        if not isinstance(key, int) or key >= 0:        # Can be changed now.
            # This constraint enables an easy implementation of __add__().
            raise ValueError("Polyline only accepts a negative integer as a deletion key.")
        del self.points[key]
        self.events.append(DeleteEvent(key))

    def __add__(self, other: 'Polygon'):
        result = Polygon()
        result.points = self.points + other.points
        result.events = self.events + other.events
        return result
