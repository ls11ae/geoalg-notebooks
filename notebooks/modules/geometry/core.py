from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Iterator, Iterable, Optional, SupportsFloat, Union
from enum import auto, Enum
from itertools import combinations
import math


EPSILON: float = 1e-9    # Chosen by testing currently implemented algorithms with the visualisation tool.


class Orientation(Enum):
    LEFT = auto()
    RIGHT = auto()
    BETWEEN = auto()
    BEFORE_SOURCE = auto()
    BEHIND_TARGET = auto()


class VerticalOrientation(Enum):
    ON = auto()
    ABOVE = auto()
    BELOW = auto()


class HorizontalOrientation(Enum):
    LEFT = auto()
    RIGHT = auto()
    EQUAL = auto()


class GeometricObject(ABC):     # TODO: Rename, move and export this.
    @abstractmethod
    def points(self) -> Iterator[Point]:
        pass

    def animation_events(self) -> Iterator[AnimationEvent]:
        return (AppendEvent(point) for point in self.points())


class Point:
    def __init__(self, x: SupportsFloat, y: SupportsFloat):
        self._x = float(x)
        self._y = float(y)

    def copy(self) -> Point:
        return Point(self._x, self._y)

    ## Properties

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    ## Operations

    def distance(self, other: Point) -> float:
        return math.sqrt((self._x - other._x)**2 + (self._y - other._y)**2)

    def dot(self, other: Point) -> float:
        return self._x * other._x + self._y * other._y

    def perp_dot(self, other: Point) -> float:
        return self._x * other._y - self._y * other._x

    def orientation(self, source: Point, target: Point, epsilon: float = EPSILON) -> Orientation:
        if source == target:
            raise ValueError("Source and target need to be two different points.")

        self_direction = self - source
        target_direction = target - source
        signed_area = self_direction.perp_dot(target_direction)

        if signed_area < -epsilon:
            return Orientation.LEFT
        elif signed_area > epsilon:
            return Orientation.RIGHT
        else:
            a = self_direction.dot(target_direction) / target_direction.dot(target_direction)
            # We don't need epsilon here, because the calculation of `a` ensures that
            # `a == 0.0` if `self == source`, whereas `a == 1.0` if `self == target`.
            if a < 0.0:
                return Orientation.BEFORE_SOURCE
            elif a > 1.0:
                return Orientation.BEHIND_TARGET
            else:
                return Orientation.BETWEEN
            
    def vertical_orientation(self, line_segment: LineSegment, epsilon: float = EPSILON) -> VerticalOrientation:
        """ Checks whether the point lies on the given line segment or one the line induced by it.
        """
        if line_segment.left.x == line_segment.right.x:  # Vertical line segment. This could be simplified if just used for the point location in notebook 04, because it ensures the point is always between the endpoints of the line segment in horizontal order.
            if self.x < line_segment.left.x:
                return VerticalOrientation.ABOVE
            elif self.x > line_segment.left.x:
                return VerticalOrientation.BELOW
            return VerticalOrientation.ON  # Case x1 = x = x2 (See [1], page 139)
        y = line_segment.y_from_x(self.x)
        if y - self.y < -epsilon:
            return VerticalOrientation.ABOVE
        if y - self.y > epsilon:
            return VerticalOrientation.BELOW
        return VerticalOrientation.ON

    def horizontal_orientation(self, other_point: Point) -> HorizontalOrientation:
        """ Checks whether the point lies to the left or the right of the given point.
        It uses a symbolic shear transform, i.e. lexicographical order.
        """
        if self == other_point:
            return HorizontalOrientation.EQUAL
        elif self.x < other_point.x or (self.x == other_point.x and self.y < other_point.y):
            return HorizontalOrientation.LEFT
        else:
            return HorizontalOrientation.RIGHT
    
    def close_to(self, other_point: Point, epsilon: float = EPSILON) -> bool:
        return self.distance(other_point) < epsilon

    ## Magic methods
        
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return self._x == other._x and self._y == other._y
    
    def __hash__(self) -> int:
        return hash((self._x, self._y))
    
    def __repr__(self) -> str:
        return f"Point: ({self._x}, {self._y})"

    def __add__(self, other: Any) -> Point:
        if not isinstance(other, Point):
            return NotImplemented

        return Point(self._x + other._x, self._y + other._y)

    def __sub__(self, other: Any) -> Point:
        if not isinstance(other, Point):
            return NotImplemented

        return Point(self._x - other._x, self._y - other._y)

    def __rmul__(self, other: Any) -> Point:
        try:
            x = float(other * self._x)
            y = float(other * self._y)
        except Exception:
            return NotImplemented

        return Point(x, y)

    def __round__(self, ndigits: Optional[int] = None) -> Point:
        return Point(round(self._x, ndigits), round(self._y, ndigits))

class PointReference(Point):    # TODO: Make this a generic type for points with attributes.
    def __init__(self, container: list[Point], position: int):
        self._container = container
        self._position = position

    def copy(self) -> PointReference:
        return PointReference([point.copy() for point in self.container], self._position)

    @property
    def container(self) -> list[Point]:
        return self._container

    @property
    def position(self) -> int:
        return self._position

    @property
    def point(self) -> Point:
        return self._container[self._position]

    @property
    def x(self) -> float:
        return self.point.x

    @property
    def y(self) -> float:
        return self.point.y

    @property
    def _x(self) -> float:
        return self.point.x

    @property
    def _y(self) -> float:
        return self.point.y

    def __repr__(self) -> str:
        return f"({self._x}, {self._y})+{self.container}"


class Line:
    def __init__(self, p1: Point, p2: Point):
        self._p1 = p1
        self._p2 = p2

    def copy(self) -> Line:
        return Line(self._p1, self._p2)
    
    def getIntersection(self, other : Line, epsilon: float = EPSILON) -> Line | Point | None :
        denominator = (self.p1.x - self.p2.x) * (other.p1.y - other.p2.y) - (self.p1.y - self.p2.y) * (other.p1.x - other.p2.x)
        ##lines are parallel or coincident
        if(abs(denominator) < epsilon):
            ##check if p1, p2 are collinear with other.p1
            x1, y1 = self.p2.x - self.p1.x, self.p2.y - self.p1.y
            x2, y2 = other.p1.x - self.p1.x, other.p1.y - self.p1.y
            if(abs(x1 * y2 - x2 * y2) < epsilon):
                ##lines are identical, so just return a line as intersection
                return self
            ##lines are parallel but not on top of each other, so no intersection exists
            return None
        xNumerator = (self.p1.x*self.p2.y - self.p1.y*self.p2.x) * (other.p1.x - other.p2.x) - (self.p1.x - self.p2.x) * (other.p1.x*other.p2.y - other.p1.y*other.p2.x)
        yNumerator = (self.p1.x*self.p2.y - self.p1.y*self.p2.x) * (other.p1.y - other.p2.y) - (self.p1.y - self.p2.y) * (other.p1.x*other.p2.y - other.p1.y*other.p2.x)
        return Point(xNumerator / denominator, yNumerator / denominator)
        

    '''
    These methods move the given point such that one coordinate is equal to the given value.

    This is need for drawing since the canvas can only draw lines from point to point without extending them.
    So instead the points on the line can be moved to outside the frame of the canvas so that it looks like a full line is drawn

    The methods fail if a line is horizontal and the y coordinate is changed or if a line is vertical and the x coordinate is changed
    '''
    #move p1 such that it has the given x coordinate
    def move_p1_x(self, new_x : float):
        intersection = self.getIntersection(Line(Point(new_x, 0), Point(new_x, 1000)))
        if type(intersection) is None:
            #lines are parallel, impossible to change coordinate
            return False
        if type(intersection) is Line:
            #lines are identical
            return False
        self._p1 = intersection
        return True

    #move p2 such that it has the given x coordinate
    def move_p2_x(self, new_x : float):
        intersection = self.getIntersection(Line(Point(new_x, 0), Point(new_x, 1000)))
        if type(intersection) is None:
            #lines are parallel, impossible to change coordinate
            return False
        if type(intersection) is Line:
            #lines are identical
            return False
        self._p2 = intersection
        return True

    #move p1 such that it has the given y coordinate
    def move_p1_y(self, new_y : float):
        intersection = self.getIntersection(Line(Point(0, new_y), Point(1000, new_y)))
        if type(intersection) is None:
            #lines are parallel, impossible to change coordinate
            return False
        if type(intersection) is Line:
            #lines are identical
            return False
        self._p1 = intersection
        return True

    #move p2 such that it has the given y coordinate
    def move_p2_y(self, new_y : float):
        intersection = self.getIntersection(Line(Point(0, new_y), Point(1000, new_y)))
        if type(intersection) is None:
            #lines are parallel, impossible to change coordinate
            return False
        if type(intersection) is Line:
            #lines are identical
            return True
        self._p2 = intersection
        return True


    ## Properties
    @property
    def p1(self) -> float:
        return self._p1

    @property
    def p2(self) -> float:
        return self._p2

    def __repr__(self) -> str:
        return f"Line: ({self._p1}, {self._p2})"


class LineSegment:
    def __init__(self, p: Point, q: Point):
        if p == q:
            raise ValueError("A line segment needs two different endpoints.")
        if p.y > q.y or (p.y == q.y and p.x < q.x):
            self._upper = p
            self._lower = q
        else:
            self._upper = q
            self._lower = p

    ## Properties

    @property
    def upper(self) -> Point:
        return self._upper

    @property
    def lower(self) -> Point:
        return self._lower
    
    @property
    def left(self) -> Point:
        return self._upper if self._upper.x < self._lower.x or (self._upper.x == self._lower.x and self._upper.y < self._lower.y) else self._lower

    @property
    def right(self) -> Point:
        return self._upper if self._upper.x > self._lower.x or (self._upper.x == self._lower.x and self._upper.y > self._lower.y) else self._lower

    ## Operation(s)

    def intersection(self, other: LineSegment, epsilon: float = EPSILON) -> Union[Point, LineSegment, None]:
        self_direction = self._upper - self._lower
        other_direction = other._upper - other._lower
        lower_offset = other._lower - self._lower
        signed_area_sd_od = self_direction.perp_dot(other_direction)
        signed_area_lo_od = lower_offset.perp_dot(other_direction)
        signed_area_lo_sd = lower_offset.perp_dot(self_direction)

        if abs(signed_area_sd_od) > epsilon:
            a = signed_area_lo_od / signed_area_sd_od
            b = signed_area_lo_sd / signed_area_sd_od
            if -epsilon <= a <= 1.0 + epsilon and -epsilon <= b <= 1.0 + epsilon:
                return self._lower + a * self_direction
            else:
                return None

        # Check both signed areas to ensure consistency and increase robustness.
        if abs(signed_area_lo_od) <= epsilon or abs(signed_area_lo_sd) <= epsilon:
            self_direction_dot = self_direction.dot(self_direction)
            upper_offset = other._upper - self._lower
            a_lower = lower_offset.dot(self_direction) / self_direction_dot
            a_upper = upper_offset.dot(self_direction) / self_direction_dot

            # The inner min/max operations aren't needed in theory, because `a_lower < a_upper`
            # should always hold. However, inaccuracies might somehow invalidate that.
            a_lower_clipped = max(0.0, min(a_lower, a_upper))
            a_upper_clipped = min(1.0, max(a_lower, a_upper))
            upper = self._lower + a_upper_clipped * self_direction
            if a_lower_clipped == a_upper_clipped:
                return upper
            elif a_lower_clipped < a_upper_clipped:
                lower = self._lower + a_lower_clipped * self_direction
                return LineSegment(upper, lower)
            else:
                return None

        return None

    def y_from_x(self, x):
        if self.upper.x == self.lower.x:
            raise Exception(f"Can not give y coordinate for vertical segment {self}")
        return (x - self.upper.x) / (self.lower.x - self.upper.x) * (self.lower.y - self.upper.y) + self.upper.y
    
    def slope(self) -> SupportsFloat:
        if self.left.x - self.right.x == 0:
            return float("inf")  # vertical segment
        return (self.left.y - self.right.y) / (self.left.x - self.right.x)

    ## Magic methods

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, LineSegment):
            return NotImplemented

        return self.upper == other.upper and self.lower == other.lower

    def __hash__(self) -> int:
        return hash((self.upper, self.lower))

    def __repr__(self) -> str:
        return f"{self.left}--{self.right}"


class Rectangle:
    def __init__(self, point_0: Point, point_1: Point) -> None:
        if point_0.x < point_1.x:
            self._left = point_0.x
            self._right = point_1.x
        else:
            self._left = point_1.x
            self._right = point_0.x

        if point_0.y < point_1.y:
            self._lower = point_0.y
            self._upper = point_1.y
        else:
            self._lower = point_1.y
            self._upper = point_0.y

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    @property
    def upper(self):
        return self._upper

    @property
    def lower(self):
        return self._lower
    

class AnimationEvent(ABC):      # TODO: Maybe use an Enum instead...
    @abstractmethod
    def execute_on(self, points: list[Point]):
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
