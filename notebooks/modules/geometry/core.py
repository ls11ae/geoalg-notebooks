from __future__ import annotations
from typing import Any, Optional, SupportsFloat, Union, Generic, TypeVar
from enum import auto, Enum
import math

EPSILON: float = 1e-9 # Chosen by testing currently implemented algorithms with the visualisation tool.

P = TypeVar("P") # type variable for points with generic data

class Orientation(Enum):
    "locates a point relative to the endpoints of a line segment"
    LEFT = auto()
    RIGHT = auto()
    BETWEEN = auto()
    BEFORE_SOURCE = auto()
    BEHIND_TARGET = auto()

class VerticalOrientation(Enum):
    "locates a point relative to a line"
    ON = auto()
    ABOVE = auto()
    BELOW = auto()

class HorizontalOrientation(Enum):
    "locates a point relative to another point (lexicograhical order)"
    LEFT = auto()
    RIGHT = auto()
    EQUAL = auto()


class Point:
    """Point representation used by many other objects.

    Attributes
    ----------
    _x : float
        x coordinate
    _y : float
        y coordinate
    _tag : int
        used to distinguish different types of points during drawing, set according to your needs

    Methods
    -------
    copy()
        returns an exact copy of this point
    distance(other)
        returns euclidian distance to another point
    dot(other)
        returns the dot product between the vectors defined by the two points and the origin
    perp_dot(other)
        TODO:comment
    orientation(source, target, epsilon)
        returns the orientation relative to target and source (see Orientation Enum)
    vertical_orientation(lineSegment)
        returns the relative position to the given line
        TODO: replace with line once linesegment inherits from line
    horizontal_orientation(other)
        returns the lexicographical order relative to the given point
    """

    def __init__(self, x: SupportsFloat, y: SupportsFloat, tag : int = 0):
        """
        Parameters
        ----------
        tag : int
            used to distinguish different points when drawing, use as needed (default is 0)
        """

        self._x = float(x)
        self._y = float(y)
        self._tag = tag

    def copy(self) -> Point:
        return Point(self._x, self._y, self._tag)

    # -------- methods --------

    def distance(self, other: Point) -> float:
        return math.sqrt((self._x - other._x)**2 + (self._y - other._y)**2)

    def dot(self, other: Point) -> float:
        "interprets points as vectors to those points"
        return self._x * other._x + self._y * other._y

    def perp_dot(self, other: Point) -> float:
        "interprets points as vectors to those points"
        return self._x * other._y - self._y * other._x

    def orientation(self, source: Point, target: Point, epsilon: float = EPSILON) -> Orientation:
        """returns the orientation relative to target and source (see Orientation Enum)
        
        Parameters
        ----------
        source : Point
            first point of the linesegment
        target : Point
            second point of the linesegment
        epsilon : float
            used for numerical stability, standard value should work well
        
        Returns
        -------
        Orientation.LEFT
            if the point is left of the line from source to target
        Orientation.RIGHT
            if the point is right of the line from source to target
        Orientation.BEFORE_SOURCE
            if the point is on the line and lexicographically before source
        Orientation.AFTER_TARGET
            if the point is on the line and lexicographically after target
        Orientation.ON
            if the point is on the line and lexicographicall between source and target

        Raises
        ------
        ValueError
            if target and source are equal  
        """
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
            #TODO: can be done without division
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
        """Checks whether the point lies on the given line segment or one the line induced by it.

        Parameters
        ----------
        line_segment : LineSegment
            TODO: make generic for line, linesegment and point
        epsilon : float
            used for numerical stability, standard value should work well
        
        Returns
        -------
        VerticalOrientation.ABOVE
            if the point is above the induced line
        VerticalOrientation.BELOW
            if the point is below the induced line
        VerticalOrientation.ON
            if the point is on the induced line
        
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
        """Returns the position in lexicographical order relative to the other point using 
        a symbolic shear transform.

        Parameters
        ----------
        other_point : Point
            point relative to which the position is returned
        
        Returns
        -------
        HorizontalOrientation.EQUAL
            if the points are equal 
        HorizontalOrientation.LEFT
            if other_point is later in lexicographical order
        HorizontalOrientation.RIGHT
            if other_point is earlier in lexicographical order 
        
        """
        if self == other_point:
            return HorizontalOrientation.EQUAL
        elif self.x < other_point.x or (self.x == other_point.x and self.y < other_point.y):
            return HorizontalOrientation.LEFT
        else:
            return HorizontalOrientation.RIGHT
    
    def close_to(self, other_point: Point, epsilon: float = EPSILON) -> bool:
        return self.distance(other_point) < epsilon

    ## -------- properties --------

    @property
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self,value):
        self._x = value

    @property
    def y(self) -> float:
        return self._y

    @y.setter
    def y(self,value):
        self._y = value

    @property
    def tag(self) -> int:
        return self._tag

    @tag.setter
    def tag(self,value):
        self._tag = value

    ## -------- magic methods --------
        
    def __eq__(self, other : Any) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return self._x == other._x and self._y == other._y

    def __copy__(self) -> Point:
        return Point(self.x, self.y)
    
    def __deepcopy__(self, memo) -> Point:
        return Point(self.x, self.y)
    
    def __hash__(self) -> int:
        return hash((self._x, self._y))

    def __str__(self) -> str:
        return f"({self._x}, {self._y})"

    def __add__(self, other: Any) -> Point:
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self._x + other._x, self._y + other._y)

    def __sub__(self, other: Any) -> Point:
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self._x - other._x, self._y - other._y)

    def __mul__(self, other : Any) -> Point:
        if not isinstance(other, Point):
            return NotImplemented
        return Point(self.x * other.x, self.y * other.y)
    
    def __rmul__(self, other: Any) -> Point:
        try:
            x = float(other * self._x)
            y = float(other * self._y)
        except Exception:
            return NotImplemented
        return Point(x, y)

    def __round__(self, ndigits: Optional[int] = None) -> Point:
        return Point(round(self._x, ndigits), round(self._y, ndigits))
    

# TODO: move all sublcasses of point extension to own file
class PointExtension(Point, Generic[P]):
    """Extends point by a generic data parameter. 
    
    Attributes
    ----------
    data : P
        generic data object to hold any necessary information (eg.: outgoing edges)
    """
    def __init__(self, x: SupportsFloat, y: SupportsFloat, data : P = None, tag : int = 0):
        super().__init__(x, y, tag)
        self._data = data
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        self._data = data

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, PointExtension):
            return NotImplemented
        return self._x == other._x and self._y == other._y and self._data.__eq__(other.data)


class Line:
    """A line defined by two points on the line.

    Attributes
    ----------
    _p1 : Point
        a point on the line
    _p2 : Point
        a different point on the line
    
    Methods
    -------
    intersection(other)
        returns the intersection between two lines or a line and a line segment
    """

    def __init__(self, p1: Point, p2: Point):
        if p1 == p2:
            raise ValueError("A line needs two different endpoints.")
        self._p1 : Point = p1
        self._p2 : Point = p2

    def copy(self) -> Line:
        return Line(self._p1, self._p2)
    
    def intersection(self, other : Line, epsilon: float = EPSILON) -> Line | LineSegment | Point | None :
        #https://en.wikipedia.org/wiki/Line–line_intersection#Given_two_points_on_each_line
        denominator = (self.p1.x - self.p2.x) * (other.p1.y - other.p2.y) - (self.p1.y - self.p2.y) * (other.p1.x - other.p2.x)
        if abs(denominator) < epsilon: #lines are parallel/identical
            # check if other.p1 is on self using cross product
            cross = (other.p1.x - self.p1.x) * (self.p2.y - self.p1.y) - (other.p1.y - self.p1.y) * (self.p2.x - self.p1.x)
            if abs(cross) < epsilon:
                #lines are identical
                if isinstance(other, LineSegment):
                    return LineSegment(other.p1, other.p2)
                return Line(self.p1, self.p2)
            #lines are parallel
            return None
        #lines are neither parallel nor idendical, calculate intersection
        xNumerator = (self.p1.x*self.p2.y - self.p1.y*self.p2.x) * (other.p1.x - other.p2.x) - (self.p1.x - self.p2.x) * (other.p1.x*other.p2.y - other.p1.y*other.p2.x)
        yNumerator = (self.p1.x*self.p2.y - self.p1.y*self.p2.x) * (other.p1.y - other.p2.y) - (self.p1.y - self.p2.y) * (other.p1.x*other.p2.y - other.p1.y*other.p2.x)
        #in case other is a line segment, check if candidate is between endpoints
        if isinstance(other, LineSegment):
            #to avoid problems with vertical/horizontal segments, check the coordinate with larger difference
            dxo, dyo = other.upper.x - other.lower.x, other.upper.y - other.lower.y
            if abs(dxo) > abs(dyo):
                #x increases more than y
                if (other.lower.x * denominator) <= xNumerator <= (other.upper.x * denominator):
                    return Point(xNumerator / denominator, yNumerator / denominator)
            else:
                #x increases more than y
                if (other.lower.y * denominator) <= yNumerator <= (other.upper.y * denominator):
                    return Point(xNumerator / denominator, yNumerator / denominator)
            return None
        return Point(xNumerator / denominator, yNumerator / denominator)

    # -------- properties --------

    @property
    def p1(self) -> Point:
        return self._p1

    @property
    def p2(self) -> Point:
        return self._p2

    def slope(self) -> float:
        "Returns infinity if p1.x == p2.x"
        if self.p1.x == self.p2.x:
            return float("inf")  # vertical segment
        return (self.p2.y - self.p1.y) / (self.p2.x - self.p1.x)
    
    def y_from_x(self, x) -> float:
        "Throws exception if p1.x == p2.x"
        if self.p1.x == self.p2.x:
            raise Exception(f"Can not give y coordinate for vertical line: {self}")
        return self.slope() * (x - self.p1.x) + self.p1.y
    
    def x_from_y(self, y) -> float:
        "Throws exception if p1.y == p2.y"
        if self.p1.y == self.p2.y:
            raise Exception(f"Can not give x coordinate for horizontal line: {self}")
        return (y - self.p1.y) / self.slope() + self.p1.x

    # -------- magic methods --------

    def __eq__(self, other : Any) -> bool:
        if not isinstance(other, Line):
            return NotImplemented
        if self.p1 == other.p1 and self.p2 == other.p2:
            return True
        #lines can be the same even if they are defined by different points
        denominator = (self.p1.x - self.p2.x) * (other.p1.y - other.p2.y) - (self.p1.y - self.p2.y) * (other.p1.x - other.p2.x)
        if abs(denominator) < EPSILON:
            ##check if p1, p2 are collinear with other.p1
            x1, y1 = self.p2.x - self.p1.x, self.p2.y - self.p1.y
            x2, y2 = other.p1.x - self.p1.x, other.p1.y - self.p1.y
            if abs(x1 * y1 - x2 * y2) < EPSILON:
                return True
        return False

    def __copy__(self) -> Line:
        return Line(self.p1, self.p2)
    
    def __deepcopy__(self, memo) -> Line:
        return Line(Point(self.p1.x, self.p1.y), Point(self.p2.x, self.p2.y))

    def __hash__(self) -> int:
        return hash((self.p1, self.p2))

    def __str__(self) -> str:
        return f"(--{self.p1}->{self.p2}--)"


class LineSegment(Line):
    """A linesegment represented by a lower and upper point
    
    Attributes
    ----------
    lower : Point
        the lower of the two endpoints
    upper : Point
        the upper of the two endpoints
    left : Point
        the left of the two points
    right : Point
        the right of the two points

    Methods
    -------
    to_Line()
        returns the line induced by this segment
    intersection(other)
        returns the intersection with the other linesegment
    y_from_x(x)
        returns the y coodinate at the given x coordinate
    slope()
        returns the slope of this segment
    """

    def __init__(self, p: Point, q: Point):
        super().__init__(p,q)
        if p == q:
            raise ValueError("A line segment needs two different endpoints.")
        if p.y > q.y or (p.y == q.y and p.x < q.x):
            self._upper = p
            self._lower = q
        else:
            self._upper = q
            self._lower = p

    # -------- properties --------

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

    # -------- methods --------

    def line(self) -> Line:
        return Line(self.left, self.right)

    def intersection(self, other: LineSegment, epsilon: float = EPSILON) -> Union[Point, LineSegment, None]:
        if type(other) is Line and not type(other) is LineSegment:
            return other.intersection(self)
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

    # -------- magic methods --------

    def __eq__(self, other : Any) -> bool:
        if not isinstance(other, LineSegment):
            return NotImplemented
        return self.upper == other.upper and self.lower == other.lower
    
    def __copy__(self, other : Any) -> LineSegment:
        return LineSegment(self.lower, self.upper)
    
    def __deepcopy__(self, other : Any, memo) -> LineSegment:
        return LineSegment(Point(self.left.x, self.lower.y), Point(self.right.x, self.upper.y))
    
    def __hash__(self) -> int:
        return hash((self.upper, self.lower))

    def __str__(self) -> str:
        return f"LS({self.left}->{self.right})"


class Rectangle:
    """
    An axis alinged Rectangle represented by left, right, lower and uper boundary

    Attributes
    ----------
    _left : float
        the left boundary of the rectangle
    _right : float
        the right boundary of the rectangle
    _lower : float
        the lower boundary of the rectangle
    _upper : float
        the upper boundary of the rectangle

    Methods
    -------
    isInside(point)
        returns wether the given point is inside the rectangle or not
    isOnBoundary(point)
        returns wether the given point is on the boundary or not
    isOutside(point)
        returns wether the given point is outside the rectangle or not 
        (equal to !isInside and !isOnBoundary)
    expand(point)
        increases the rectangles boundary to contain the given point
        does nothing if the point is already within the boundary
    points()
        returns the four corner points in clockwise order, starting at the bottom left
    """

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

    # -------- methods --------

    def isInside(self, point : Point) -> bool:
        return (point.x > self.left) and (point.x < self.right) and (point.y > self.lower) and (point.y < self.upper)
    
    def isOnBoundary(self, point : Point) -> bool:
        return ((point.x == self.left or point.x == self.right) and point.y > self.lower and point.y < self.upper) or (
                (point.y == self.lower or point.y == self.upper) and point.x > self.left and point.x < self.right)

    def isOutside(self, point : Point) -> bool:
        return (point.x < self.left) or (point.x > self.right) or (point.y < self.lower) or (point.y > self.upper)

    def expand(self, point : Point):
        if point.x < self.left:
            self._left = point.x
        if point.x > self.right:
            self._right = point.x
        if point.y < self.lower:
            self._lower = point.y
        if point.y > self.upper:
            self._upper = point.y

    def points(self) -> list[Point]:
        return [Point(self.left, self.lower), 
                Point(self.left, self.upper), 
                Point(self.right, self.upper), 
                Point(self.right, self.lower)]

    # -------- properties --------

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper

    # -------- magic methods --------

    def __eq__(self, other : Any) -> bool:
        if not isinstance(other, Rectangle):
            return NotImplemented
        return self.left == other.left and self.right == other.right and self.lower == other.lower and self.upper == other.upper 

    def __copy__(self) -> Rectangle:
        return Rectangle(Point(self.left, self.lower), Point(self.right, self.upper))
    
    def __deepcopy__(self) -> Rectangle:
        return Rectangle(Point(self.left, self.lower), Point(self.right, self.upper))

    def __str__(self) -> str:
        return f"Rectangle({Point(self.left, self.lower)}, {Point(self.right, self.upper)})"