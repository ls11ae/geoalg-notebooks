from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Iterable

from ..geometry import LineSegment, Point, Orientation as ORT, Rectangle
from .objects import Face
from .dcel import DoublyConnectedEdgeList


class PointLocation:
    def __init__(self, bounding_box: Rectangle, segments: set[LineSegment] = []) -> None:
        self._vertical_decomposition = VerticalDecomposition(bounding_box)
        initial_face = self._vertical_decomposition.trapezoids[0]
        self._search_structure = VDSearchStructure(initial_face)
        self._i = 0

    def insert(self, line_segment: LineSegment) -> None:
        left_point_face = self._search_structure._root.search(line_segment.left)
        face_indicies = [0, 2, 6, 0]
        left_point_face = self._vertical_decomposition._trapezoids[face_indicies[self._i]]
        self._i = self._i + 1
        self._vertical_decomposition.update(VDLineSegment.from_line_segment(line_segment), left_point_face)


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
    
    def update(self, line_segment: VDLineSegment, left_point_face: VDFace) -> list[VDFace]: # Maybe return tuple of intersected and created trapezoids
        # Find all other k intersected trapezoids (via neighbors) in O(k) time
        intersected_trapezoids: list[VDFace] = []
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
            
        if intersected_trapezoids == []:  
            # edge case: both points lie in the same trapezoid. replace it by four new trapezoids
            trapezoid_top = VDFace(left_point_face.top_line_segment, line_segment, line_segment.left, line_segment.right)
            trapezoid_bottom = VDFace(line_segment, left_point_face.bottom_line_segment, line_segment.left, line_segment.right)
            trapezoid_left = VDFace(left_point_face.top_line_segment, left_point_face.bottom_line_segment, left_point_face.left_point, line_segment.left)
            trapezoid_right = VDFace(left_point_face.top_line_segment, left_point_face.bottom_line_segment, line_segment.right, left_point_face.right_point)
            trapezoid_left.neighbors = [trapezoid_top, left_point_face.upper_left_neighbor, left_point_face.lower_left_neighbor, trapezoid_bottom]
            trapezoid_right.neighbors = [left_point_face.upper_right_neighbor, trapezoid_top, trapezoid_bottom, left_point_face.lower_right_neighbor]
            
            self._trapezoids.remove(left_point_face)
            self._trapezoids.extend([trapezoid_left, trapezoid_top, trapezoid_bottom, trapezoid_right])
            return [trapezoid_left, trapezoid_top, trapezoid_bottom, trapezoid_right]

        # update VD (also in O(k) time): new faces, neighbors 

        # Split first and last trapezoid into three trapezoids
        # left endpoint:
        above_face_l = VDFace(left_point_face.top_line_segment, line_segment, line_segment.left, left_point_face.right_point)
        below_face_l = VDFace(line_segment, left_point_face.bottom_line_segment, line_segment.left, left_point_face.right_point)
        above_face_l.neighbors = [left_point_face.upper_right_neighbor, left_point_face, None, left_point_face.lower_right_neighbor]
        below_face_l.neighbors = [left_point_face.upper_right_neighbor, None, left_point_face, left_point_face.lower_right_neighbor]
        left_point_face.right_point = line_segment.left
        left_point_face.neighbors = [above_face_l, left_point_face.upper_left_neighbor, left_point_face.lower_left_neighbor, below_face_l]

        # right endpoint
        right_point_face = intersected_trapezoids.pop()
        above_face_r = VDFace(right_point_face.top_line_segment, line_segment, right_point_face.left_point, line_segment.right)
        below_face_r = VDFace(line_segment, right_point_face.bottom_line_segment, right_point_face.left_point, line_segment.right)
        above_face_r.neighbors = [right_point_face, right_point_face.upper_left_neighbor, right_point_face.lower_left_neighbor, None]
        below_face_r.neighbors = [None, right_point_face.upper_left_neighbor, right_point_face.lower_left_neighbor, right_point_face]
        right_point_face.left_point = line_segment.right
        right_point_face.neighbors = [right_point_face.upper_right_neighbor, above_face_r, below_face_r, right_point_face.lower_right_neighbor]

        # Shorten vertical extensions abut on the LS. => Merge trapezoids along the line-segment.
        top_left_trapezoid = above_face_l
        bottom_left_trapezoid = below_face_l
        for trapezoid in intersected_trapezoids:
            if trapezoid.left_point.orientation(line_segment.left, line_segment.right) == ORT.LEFT:
                # Merge below LS
                bottom_left_trapezoid.right_point = trapezoid.right_point

                trapezoid.bottom_line_segment = line_segment
                trapezoid.lower_left_neighbor = top_left_trapezoid
                top_left_trapezoid = trapezoid
            elif trapezoid.left_point.orientation(line_segment.left, line_segment.right) == ORT.RIGHT:
                # Merge above LS
                top_left_trapezoid.right_point = trapezoid.right_point

                trapezoid.top_line_segment = line_segment
                trapezoid.upper_left_neighbor = bottom_left_trapezoid
                bottom_left_trapezoid = trapezoid
            else:
                raise RuntimeError(f"Point {trapezoid.left_point} must not lie on line induced by the line segment {line_segment}")

        # Merge with last face
        kept_face = None
        if above_face_r.left_point.orientation(line_segment.left, line_segment.right) == ORT.LEFT:
            # Merge below LS (below_face_r is discarded)
            bottom_left_trapezoid.right_point = line_segment.right
            bottom_left_trapezoid.lower_right_neighbor = right_point_face
            bottom_left_trapezoid.upper_right_neighbor = above_face_r
            kept_face = above_face_r

        elif trapezoid.left_point.orientation(line_segment.left, line_segment.right) == ORT.RIGHT:
            # Merge above LS (above_face_r is discarded)
            top_left_trapezoid.right_point = line_segment.right
            top_left_trapezoid.upper_right_neighbor = right_point_face
            bottom_left_trapezoid.lower_right_neighbor = below_face_r
            kept_face = below_face_r
        else:
            raise RuntimeError(f"Point {trapezoid.left_point} must not lie on line induced by the line segment {line_segment}")

        self._trapezoids.extend([above_face_l, below_face_l, kept_face])
        return [above_face_l, below_face_l, kept_face]
            

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

    @left_point.setter
    def left_point(self, point):
        self._left_point = point

    @property
    def right_point(self):
        return self._right_point
    
    @right_point.setter
    def right_point(self, point):
        self._right_point = point
    
    @property
    def neighbors(self):
        return self._neighbors
    
    @neighbors.setter
    def neighbors(self, new_neighbors: Iterable[Optional[VDFace]]):
        if len(new_neighbors) != 4:
            raise Exception(f"Need exactly four optional faces for setting neighbors.")
        self.upper_right_neighbor = new_neighbors[0]
        self.upper_left_neighbor = new_neighbors[1]
        self.lower_left_neighbor = new_neighbors[2]
        self.lower_right_neighbor = new_neighbors[3]
    
    @property
    def upper_right_neighbor(self):
        return self._neighbors[0]
    
    @upper_right_neighbor.setter
    def upper_right_neighbor(self, new_neighbor: VDFace):
        self._neighbors[0] = new_neighbor
        if new_neighbor is not None:
            new_neighbor._neighbors[1] = self
            

    @property
    def upper_left_neighbor(self):
        return self._neighbors[1]
    
    @upper_left_neighbor.setter
    def upper_left_neighbor(self, new_neighbor: VDFace):
        self._neighbors[1] = new_neighbor
        if new_neighbor is not None:
            new_neighbor._neighbors[0] = self
    
    @property
    def lower_left_neighbor(self):
        return self._neighbors[2]
    
    @lower_left_neighbor.setter
    def lower_left_neighbor(self, new_neighbor: VDFace):
        self._neighbors[2] = new_neighbor
        if new_neighbor is not None:
            new_neighbor._neighbors[3] = self
    
    @property
    def lower_right_neighbor(self):
        return self._neighbors[3]
    
    @lower_right_neighbor.setter
    def lower_right_neighbor(self, new_neighbor: VDFace):
        self._neighbors[3] = new_neighbor
        if new_neighbor is not None:
            new_neighbor._neighbors[2] = self
    
    def contains(self, point: Point) -> bool:
        return self.left_point.x < point.x < self._right_point.x \
                and point.orientation(self._top_line_segment.left, self._top_line_segment.right) == ORT.RIGHT \
                and point.orientation(self._bottom_line_segment.left, self._bottom_line_segment.right) == ORT.LEFT
            
    def __repr__(self) -> str:
        return f"Top-LS: {self._top_line_segment} | Bottom-LS: {self._bottom_line_segment} | Left-P: {self._left_point} | Right-P: {self._right_point}"

class VDLineSegment(LineSegment):
    def __init__(self, p: Point, q: Point):
        super().__init__(p, q)
        self._above_dcel_face: Optional[Face] = None  # The original face of the planar subdivision (DCEL)

    @classmethod
    def from_line_segment(cls, line_segment: LineSegment) -> VDLineSegment:
        return VDLineSegment(line_segment.left, line_segment.right)

    @property
    def above_face(self) -> Face:
        return self._above_dcel_face
    
    @above_face.setter
    def above_face(self, face: Face):
        self._above_dcel_face = face
