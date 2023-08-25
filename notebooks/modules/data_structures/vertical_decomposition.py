from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional

from ..geometry import LineSegment, Point, Orientation as ORT, Rectangle
from .objects import Face
from .dcel import DoublyConnectedEdgeList


class PointLocation:
    def __init__(self, bounding_box: Rectangle, segments: set[LineSegment] = []) -> None:
        self._vertical_decomposition = VerticalDecomposition(bounding_box)
        initial_face = self._vertical_decomposition.trapezoids[0]
        self._search_structure = VDSearchStructure(initial_face)

    def insert(self, line_segment: LineSegment) -> None:
        left_point_face = self._search_structure._root.search(line_segment.left)
        self._vertical_decomposition.update(line_segment, left_point_face)


    # @classmethod
    # def build_vertical_decomposition(cls, segments: set[LineSegment]) -> VerticalDecomposition:
    #    # randomized incremental construction
    #    pass


class VerticalDecomposition:
    def __init__(self, bounding_box: Rectangle) -> None:
        self._bounding_box = bounding_box
        self._trapezoids: list[VDFace] = []
        # bounding box points
        upper_left = Point(bounding_box.left, bounding_box.upper)
        upper_right = Point(bounding_box.right, bounding_box.upper)
        lower_left = Point(bounding_box.left, bounding_box.lower)
        lower_right = Point(bounding_box.right, bounding_box.lower)
        top = VDLineSegment(upper_left, upper_right)
        bottom = VDLineSegment(lower_left, lower_right)
        dcel = DoublyConnectedEdgeList()
        bottom._above_dcel_face = dcel.outer_face
        initial_trapezoid = VDFace(top, bottom, upper_left, upper_right)
        self._trapezoids.append(initial_trapezoid)

    @property
    def trapezoids(self):
        return self._trapezoids
    
    def update(self, line_segment: LineSegment, left_point_face: VDFace) -> None:
        # Find all k intersected trapezoids (via neighbors) in O(k) time
        intersected_trapezoids = []
        intersected_face = left_point_face
        left, right = line_segment.left, line_segment.right
        while not intersected_face.contains(line_segment.right): 
            # Easier: rightp above/below line_segment
            intersection_y = line_segment.left.y + (intersected_face.right_point.x-left.x) / (right.x-left.x) * (right.y-left.y)
            if intersection_y > intersected_face.right_point.y:
                intersected_face = intersected_face.upper_right_neighbor
            else:
                intersected_face = intersected_face.lower_right_neighbor
            intersected_trapezoids.append(intersected_face)
            
        # update VD (also in O(k) time): new faces, neighbors 

        # Split first and last trapezoid into three trapezoids

        # Shorten vertical extensions abut on the LS. => Merge trapezoids along the line-segment.



class VDNode(ABC):
    def __init__(self) -> None:
        self._left: Optional[VDNode] = None
        self._right: Optional[VDNode] = None

    @abstractmethod
    def search(self, point: Point) -> VDFace:
        pass


class VDXNode(VDNode):
    def __init__(self, point: Point) -> None:
        super().__init__()
        self._point: Point = point

    @property
    def left(self):
        return self._left

    @property
    def right(self):
        return self._right

    def search(self, point: Point) -> VDFace:
        if point.x < self._point.x:
            return self._left.search(point)
        else:  # equality not possible in general position TODO: Make Robust using symbolic shear transform
            return self._right.search(point)


class VDYNode(VDNode):
    def __init__(self, line_segment: VDLineSegment) -> None:
        super().__init__()
        self._line_segment = line_segment

    @property
    def lower(self):
        return self._left

    @property
    def upper(self):
        return self._right

    def search(self, point: Point) -> VDFace:
        cr = point.orientation(self._line_segment.left, self._line_segment.right)
        if cr == ORT.LEFT:
            return self.upper.search(point)
        elif cr == ORT.RIGHT:
            return self.lower.search(point)
        else:
            raise RuntimeError(f"Point {point} must not lie on line induced by the line segment {self._line_segment}")


class VDLeaf(VDNode):
    def __init__(self, face: VDFace) -> None:
        self._face: VDFace = face
        self._face.search_leaf = self
        self._left = None
        self._right = None

    def search(self, point: Point) -> VDFace:
        return self._face


class VDSearchStructure:
    def __init__(self, initial_face: VDFace) -> None:
        self._root: VDNode = VDLeaf(initial_face)

    def search(self, point: Point) -> Face:
        vd_face = self._root.search(point)
        dcel_face = vd_face.bottom_line_segment.above_face
        return dcel_face


class VDFace:  # the trapezoid
    def __init__(self, top_ls: VDLineSegment, bottom_ls: VDLineSegment, left_point: Point, right_point: Point) -> None:
        self._top_line_segment: VDLineSegment = top_ls
        self._bottom_line_segment: VDLineSegment = bottom_ls
        self._left_point: Point = left_point
        self._right_point: Point = right_point
        self._search_leaf = None
        self._neighbors = [None, None, None, None]  # Up to four neighbors for each face

    @property
    def search_leaf(self):
        return self._search_leaf

    @search_leaf.setter
    def search_leaf(self, search_leaf):
        self._search_leaf = search_leaf

    @property
    def bottom_line_segment(self):
        return self._bottom_line_segment

    @property
    def top_line_segment(self):
        return self._top_line_segment

    @property
    def left_point(self):
        return self._left_point

    @property
    def right_point(self):
        return self.right_point
    
    @property
    def upper_right_neighbor(self):
        return self._neighbors[0]
    
    @property
    def upper_left_neighbor(self):
        return self._neighbors[1]
    
    @property
    def lower_left_neighbor(self):
        return self._neighbors[2]
    
    @property
    def lower_right_neighbor(self):
        return self._neighbors[3]
    
    def contains(self, point: Point) -> bool:
        return self.left_point.x < point.x < self._right_point.x \
                and point.orientation(self._top_line_segment.left, self._top_line_segment.right) == ORT.RIGHT \
                and point.orientation(self._bottom_line_segment.left, self._bottom_line_segment.right) == ORT.LEFT
            

class VDLineSegment(LineSegment):
    def __init__(self, p: Point, q: Point):
        super().__init__(p, q)
        self._above_dcel_face: Optional[Face] = None  # The original face of the planar subdivision (DCEL)

    @property
    def above_face(self) -> Face:
        return self._above_dcel_face
