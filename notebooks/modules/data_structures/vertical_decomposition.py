from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Iterable

from ..geometry import LineSegment, Point, Orientation as ORT, Rectangle
from .objects import Face
from .dcel import DoublyConnectedEdgeList


class PointLocation:
    def __init__(self, bounding_box: Rectangle = Rectangle(Point(0, 0), Point(400, 400)), segments: set[LineSegment] = []) -> None:
        self._bounding_box = bounding_box
        self._vertical_decomposition = VerticalDecomposition(bounding_box)
        initial_face = self._vertical_decomposition.trapezoids[0]
        self._search_structure = VDSearchStructure(initial_face)
        for segment in segments:
            self.insert(segment)

    def clear(self):
        self._vertical_decomposition = VerticalDecomposition(self._bounding_box)
        initial_face = self._vertical_decomposition.trapezoids[0]
        self._search_structure = VDSearchStructure(initial_face)

    def insert(self, line_segment: LineSegment) -> None:
        left_point_face = self._search_structure._root.search(line_segment.left)

        vd_line_segment = VDLineSegment.from_line_segment(line_segment)  # TODO: preprocessing of the DCEL
        self._vertical_decomposition.line_segments.append(vd_line_segment)
        unvalid_trapezoids, new_trapezoids = self._vertical_decomposition.update(vd_line_segment, left_point_face)
        unvalid_leafs = [trapezoid.search_leaf for trapezoid in unvalid_trapezoids]
        new_leafs = [VDLeaf(trapezoid) for trapezoid in new_trapezoids]  # TODO FIX bug where trapezoid is None

        if len(unvalid_leafs) == 1:  # line segment is completely in one face
            tree = VDXNode(line_segment.left)
            tree.left = new_leafs[0]
            tree.right = VDXNode(line_segment.right)
            tree.right.left = VDYNode(vd_line_segment)
            tree.right.left.upper = new_leafs[1]
            tree.right.left.lower = new_leafs[2]
            tree.right.right = new_leafs[3]
            
            success = unvalid_leafs[0].replace_with(tree)
            if not success:  # root element
                self._search_structure._root = tree
        else:
            left = unvalid_leafs.pop(0)  # leaf of the left endpoint
            tree = VDXNode(line_segment.left)
            tree.left = new_leafs[0]
            tree.right = VDYNode(vd_line_segment)
            tree.right.upper = new_leafs[1]
            tree.right.lower = new_leafs[2]
            left.replace_with(tree)  # checking for success is not necessary. The leaf node "left" cannot be the root as there are >= 2 total nodes

            right = unvalid_leafs.pop()  # leaf of the right endpoint, filled after treatment of intersected trapezoids

            other_leaf = None
            if not unvalid_leafs == []:  # left and right point do not lie in directly neighboring faces
                if unvalid_leafs[0]._face.left_point.orientation(line_segment.left, line_segment.right) == ORT.LEFT:
                    other_leaf = new_leafs[1]
                    other_leaf_orientation = ORT.RIGHT
                elif unvalid_leafs[0]._face.left_point.orientation(line_segment.left, line_segment.right) == ORT.RIGHT:
                    other_leaf = new_leafs[2]
                    other_leaf_orientation = ORT.LEFT
                else:
                    raise RuntimeError(f"Point {unvalid_leafs[0]._face.left_point} must not lie on line induced by the line segment {line_segment}")

                for i in range(0, len(unvalid_leafs)):
                    tree = VDYNode(vd_line_segment)
                    unvalid_leafs[i].replace_with(tree)

                    if unvalid_leafs[i]._face.left_point.orientation(line_segment.left, line_segment.right) == ORT.LEFT:
                        if other_leaf_orientation == ORT.LEFT:
                            other_leaf = unvalid_leafs[i-1]  # No Index out of Bounds, because of initialisation of other_leaf
                            other_leaf_orientation = ORT.RIGHT

                        tree.upper = unvalid_leafs[i]
                        tree.lower = other_leaf
                        
                    elif unvalid_leafs[i]._face.left_point.orientation(line_segment.left, line_segment.right) == ORT.RIGHT:
                        if other_leaf_orientation == ORT.RIGHT:
                            other_leaf = unvalid_leafs[i-1]
                            other_leaf_orientation = ORT.LEFT
                        
                        tree.upper = other_leaf
                        tree.lower = unvalid_leafs[i]

                    else:
                        raise RuntimeError(f"Point {unvalid_leafs[0]._face.left_point} must not lie on line induced by the line segment {line_segment}")
                    
                if new_leafs[-2]._face.left_point.orientation(line_segment.left, line_segment.right) == ORT.LEFT:
                    if other_leaf_orientation == ORT.LEFT:
                        other_leaf = unvalid_leafs[-1]
                elif new_leafs[-2]._face.left_point.orientation(line_segment.left, line_segment.right) == ORT.RIGHT:
                    if other_leaf_orientation == ORT.RIGHT:
                        other_leaf = unvalid_leafs[-1]

            # treatment of leaf of right point
            tree = VDXNode(line_segment.right)
            tree.right = new_leafs[-1]
            tree.left = VDYNode(vd_line_segment)
            if new_leafs[-2]._face.bottom_line_segment is vd_line_segment:
                tree.left.upper = new_leafs[-2]
                if other_leaf != None:
                    tree.left.lower = other_leaf
                else:
                    tree.left.lower = new_leafs[2]
                    
            elif new_leafs[-2]._face.top_line_segment is vd_line_segment:
                tree.left.lower = new_leafs[-2]
                if other_leaf != None:
                    tree.left.upper = other_leaf
                else:
                    tree.left.upper = new_leafs[2]
                    
            else:
                raise RuntimeError(f"face {new_leafs[-2]._face} needs to be directly above or below of line segment {line_segment}")
                
            right.replace_with(tree)

    # @classmethod
    # def build_vertical_decomposition(cls, segments: set[LineSegment]) -> VerticalDecomposition:
    #    # randomized incremental construction
    #    pass


class VerticalDecomposition:
    def __init__(self, bounding_box: Rectangle) -> None:
        self._bounding_box = bounding_box
        self._trapezoids: list[VDFace] = []
        self._line_segments: list[VDLineSegment] = []
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
    
    @property
    def line_segments(self):
        return self._line_segments
    
    def update(self, line_segment: VDLineSegment, left_point_face: VDFace) -> tuple[list[VDFace], list[VDFace]]:
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
            return [left_point_face], [trapezoid_left, trapezoid_top, trapezoid_bottom, trapezoid_right]

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
        if above_face_r.left_point.orientation(line_segment.left, line_segment.right) == ORT.LEFT:
            # Merge below LS (below_face_r is overriden)
            bottom_left_trapezoid.right_point = line_segment.right
            bottom_left_trapezoid.lower_right_neighbor = right_point_face
            bottom_left_trapezoid.upper_right_neighbor = above_face_r
            kept_face = above_face_r
        elif above_face_r.left_point.orientation(line_segment.left, line_segment.right) == ORT.RIGHT:
            # Merge above LS (above_face_r is overriden)
            top_left_trapezoid.right_point = line_segment.right
            top_left_trapezoid.upper_right_neighbor = right_point_face
            bottom_left_trapezoid.lower_right_neighbor = below_face_r
            kept_face = below_face_r
        else:
            raise RuntimeError(f"Point {trapezoid.left_point} must not lie on line induced by the line segment {line_segment}")

        self._trapezoids.extend([above_face_l, below_face_l, kept_face])
        return [left_point_face] + intersected_trapezoids + [right_point_face], [left_point_face, above_face_l, below_face_l, kept_face, right_point_face]
            

class VDNode(ABC):
    def __init__(self) -> None:
        self._left: Optional[VDNode] = None
        self._right: Optional[VDNode] = None
        self._parent: Optional[VDNode] = None

    @property
    def parent(self) -> Optional[VDNode]:
        return self._parent

    @abstractmethod
    def search(self, point: Point) -> VDFace:
        pass

    def replace_with(self, new_node: VDNode) -> bool:
        if self._parent == None:  # node is the root
            return False
        if self._parent._left is self:
            self._parent._left = new_node
        elif self._parent._right is self:
            self._parent._right = new_node
        else:
            raise Exception(f"{self} need to be a child of its parent {self._parent}")
        
        new_node._parent = self.parent        
        return True


class VDXNode(VDNode):
    def __init__(self, point: Point) -> None:
        super().__init__()
        self._point: Point = point

    @property
    def left(self) -> Optional[VDNode]:
        return self._left
    
    @left.setter
    def left(self, left: Optional[VDNode]):
        self._left = left
        if left != None:
            left._parent = self

    @property
    def right(self) -> Optional[VDNode]:
        return self._right
    
    @right.setter
    def right(self, right: Optional[VDNode]):
        self._right = right
        if right != None:
            right._parent = self

    def search(self, point: Point) -> VDFace:  # TODO: Make Robust using symbolic shear transform
        if point.x < self._point.x:
            return self._left.search(point)
        else:  # equality not possible in general position
            return self._right.search(point)


class VDYNode(VDNode):
    def __init__(self, line_segment: VDLineSegment) -> None:
        super().__init__()
        self._line_segment: VDLineSegment = line_segment

    @property
    def lower(self) -> Optional[VDNode]:
        return self._left
    
    @lower.setter
    def lower(self, lower: Optional[VDNode]):
        self._left = lower
        if lower != None:
            lower._parent = self

    @property
    def upper(self) -> Optional[VDNode]:
        return self._right
    
    @upper.setter
    def upper(self, upper: Optional[VDNode]):
        self._right = upper
        if upper != None:
            upper._parent = self

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
        super().__init__()
        self._face: VDFace = face
        self._face.search_leaf = self

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
        self._search_leaf: VDLeaf = None
        self._neighbors: list[VDFace] = [None, None, None, None]  # Up to four neighbors for each face

    @property
    def search_leaf(self) -> VDLeaf:
        return self._search_leaf

    @search_leaf.setter
    def search_leaf(self, search_leaf: VDLeaf):
        self._search_leaf = search_leaf

    @property
    def bottom_line_segment(self) -> VDLineSegment:
        return self._bottom_line_segment
    
    @bottom_line_segment.setter
    def bottom_line_segment(self, bottom_line_segment: VDLineSegment):
        self._bottom_line_segment = bottom_line_segment

    @property
    def top_line_segment(self) -> VDLineSegment:
        return self._top_line_segment
    
    @top_line_segment.setter
    def top_line_segment(self, top_line_segment: VDLineSegment):
        self._top_line_segment = top_line_segment

    @property
    def left_point(self) -> Point:
        return self._left_point

    @left_point.setter
    def left_point(self, point: Point):
        self._left_point = point

    @property
    def right_point(self) -> Point:
        return self._right_point
    
    @right_point.setter
    def right_point(self, point: Point):
        self._right_point = point
    
    @property
    def neighbors(self) -> list[VDFace]:
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
