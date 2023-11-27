from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Iterable, Union
import random

from ..geometry import LineSegment, Point, PointReference, VerticalOrientation as VORT, HorizontalOrientation as HORT, Rectangle, PointSequence
from .objects import Face
from .dcel import DoublyConnectedEdgeList

class PLSearchStructure(ABC):
    def query(self, point: Point):
        pass

class PointLocation:
    def __init__(self, bounding_box: Rectangle = Rectangle(Point(0, 0), Point(400, 400)), dcel: Optional[DoublyConnectedEdgeList] = None, random_seed: Optional[int] = None) -> None:
        if dcel is None:
            dcel = DoublyConnectedEdgeList()
        self._bounding_box = bounding_box
        self._dcel = dcel
        self._vertical_decomposition = VerticalDecomposition(bounding_box, dcel)
        initial_face = self._vertical_decomposition._trapezoids[0]
        self._search_structure: PLSearchStructure = VDSearchStructure(initial_face)
        # Randomized Incremental Construction
        self.build_vertical_decomposition(PointLocation.dcel_prepocessing(self._dcel), random_seed)

    def check_structure(self):
        # --- Vertical Decompostion ---
        for trapezoid in self._vertical_decomposition.trapezoids:
            # Neighbors:
            # Wrongly None
            if trapezoid.left_point is not trapezoid.top_line_segment.left and trapezoid.left_point.x > self._bounding_box.left and trapezoid.upper_left_neighbor is None:
                raise RuntimeError(f"Upper left neighbor necessary in trapezoid {trapezoid}")
            if trapezoid.left_point is not trapezoid.bottom_line_segment.left and trapezoid.left_point.x > self._bounding_box.left and trapezoid.lower_left_neighbor is None:
                raise RuntimeError(f"Lower left neighbor necessary in trapezoid {trapezoid}")
            if trapezoid.right_point is not trapezoid.top_line_segment.right and trapezoid.right_point.x < self._bounding_box.right and trapezoid.upper_right_neighbor is None:
                raise RuntimeError(f"Upper right neighbor necessary in trapezoid {trapezoid}")
            if trapezoid.right_point is not trapezoid.bottom_line_segment.right and trapezoid.right_point.x < self._bounding_box.right and trapezoid.lower_right_neighbor is None:
                raise RuntimeError(f"Lower right neighbor necessary in trapezoid {trapezoid}")

            # Wrongly not None
            if trapezoid.left_point is trapezoid.top_line_segment.left and trapezoid.upper_left_neighbor is not None:
                raise RuntimeError(f"Not allowed upper left neighbor in trapezoid {trapezoid}")
            if trapezoid.left_point is trapezoid.bottom_line_segment.left and trapezoid.lower_left_neighbor is not None:
                raise RuntimeError(f"Not allowed lower left neighbor in trapezoid {trapezoid}")
            if trapezoid.right_point is trapezoid.top_line_segment.right and trapezoid.upper_right_neighbor is not None:
                raise RuntimeError(f"Not allowed upper right neighbor in trapezoid {trapezoid}")
            if trapezoid.right_point is trapezoid.bottom_line_segment.right and trapezoid.lower_right_neighbor is not None:
                raise RuntimeError(f"Not allowed lower right neighbor in trapezoid {trapezoid}")

            # Pairwise connection
            if trapezoid.upper_right_neighbor is not None and trapezoid.upper_right_neighbor.upper_left_neighbor is not trapezoid:
                raise RuntimeError(f"Issue with upper right neighbor in trapezoid {trapezoid}")
            if trapezoid.upper_left_neighbor is not None and trapezoid.upper_left_neighbor.upper_right_neighbor is not trapezoid:
                raise RuntimeError(f"Issue with upper left neighbor in trapezoid {trapezoid}")
            if trapezoid.lower_right_neighbor is not None and trapezoid.lower_right_neighbor.lower_left_neighbor is not trapezoid:
                raise RuntimeError(f"Issue with lower right neighbor in trapezoid {trapezoid}")
            if trapezoid.lower_left_neighbor is not None and trapezoid.lower_left_neighbor.lower_right_neighbor is not trapezoid:
                raise RuntimeError(f"Issue with lower left neighbor {trapezoid.lower_left_neighbor} in trapezoid {trapezoid}")
            
            # Pairwise neighbors: "connection" points
            if trapezoid.upper_right_neighbor is not None and trapezoid.upper_right_neighbor.left_point is not trapezoid.right_point:
                raise RuntimeError(f"Issue in the pair of right point of {trapezoid} and the left point of its upper right neighbor")
            if trapezoid.lower_right_neighbor is not None and trapezoid.lower_right_neighbor.left_point is not trapezoid.right_point:
                raise RuntimeError(f"Issue in the pair of right point of {trapezoid} and the left point of its lower right neighbor")
            if trapezoid.upper_left_neighbor is not None and trapezoid.upper_left_neighbor.right_point is not trapezoid.left_point:
                raise RuntimeError(f"Issue in the pair of left point of {trapezoid} and the right point of its upper left neighbor")
            if trapezoid.lower_left_neighbor is not None and trapezoid.lower_left_neighbor.right_point is not trapezoid.left_point:
                raise RuntimeError(f"Issue in the pair of left point of {trapezoid} and the right point of its lower left neighbor")

            # Search Leaf:
            if trapezoid.search_leaf is None:
                raise RuntimeError(f"Search Leaf of trapezoid {trapezoid} is None")
            if trapezoid.search_leaf._face is not trapezoid:
                raise RuntimeError(f"Wrong connection of search leaf in trapezoid {trapezoid}")
        
        # --- Search Structure ---
        if len(self._search_structure._root.parents) != 0:
            raise RuntimeError(f"Root of search structure has parents")
        self._search_structure._root.check_structure()

    def clear(self):
        self.clear_vertical_decomposition()
        self._dcel.clear()

    def clear_vertical_decomposition(self):
        self._vertical_decomposition = VerticalDecomposition(self._bounding_box, DoublyConnectedEdgeList())
        initial_face = self._vertical_decomposition._trapezoids[0]
        self._search_structure = VDSearchStructure(initial_face)

    def insert(self, line_segment: VDLineSegment) -> None:
        # Get necessary information
        left_point_face = self._search_structure.root.search(line_segment.left, line_segment)

        # 1. Update the vertical decomposition
        unvalid_trapezoids, new_trapezoids = self._vertical_decomposition.update(line_segment, left_point_face)

        # 2. Update the search structure
        unvalid_leafs = [trapezoid.search_leaf for trapezoid in unvalid_trapezoids]
        new_leafs = [VDLeaf(trapezoid) if trapezoid is not None else None for trapezoid in new_trapezoids]
        self._search_structure.update(line_segment, unvalid_leafs, new_leafs)

    @classmethod
    def dcel_prepocessing(cls, dcel: DoublyConnectedEdgeList) -> Iterable[VDLineSegment]:
        segments: list[VDLineSegment] = []
        for edge in dcel.edges:
            if edge.origin == edge.destination:
                continue
            if edge.origin is edge.left_and_right[0]:  # Make sure only one of each Halfedges is used
                ls = VDLineSegment(edge.origin.point, edge.destination.point)
                ls.above_face = edge.incident_face
                segments.append(ls)
        return segments
                

    def build_vertical_decomposition(self, segments: Iterable[LineSegment], random_seed: Optional[int] = None) -> VerticalDecomposition:
        self.clear_vertical_decomposition()
        # Randomized incremental construction
        if random_seed is not None:
            random.seed(random_seed)
        random.shuffle(segments)
        for segment in segments:
            self.insert(segment)
            # self.check_structure()  # Just for testing, takes a considerable amount of time
            # print(f"Check successful after insertion of LS {segment}")


class VerticalDecomposition:
    def __init__(self, bounding_box: Rectangle, dcel: DoublyConnectedEdgeList) -> None:
        self._bounding_box = bounding_box
        self._trapezoids: list[VDFace] = []
        self._line_segments: list[VDLineSegment] = []
        # Compute bounding box points
        upper_left = Point(bounding_box.left, bounding_box.upper)
        upper_right = Point(bounding_box.right, bounding_box.upper)
        lower_left = Point(bounding_box.left, bounding_box.lower)
        lower_right = Point(bounding_box.right, bounding_box.lower)

        top = VDLineSegment(upper_left, upper_right)
        bottom = VDLineSegment(lower_left, lower_right)
        bottom._above_dcel_face = dcel.outer_face
        initial_trapezoid = VDFace(top, bottom, upper_left, upper_right)
        self._trapezoids.append(initial_trapezoid)
        self._point_sequence: PointSequence = PointSequence()

    # region properties

    @property
    def trapezoids(self):
        return self._trapezoids
    
    @property
    def line_segments(self):
        return self._line_segments
    
    # endregion
    
    def update(self, line_segment: VDLineSegment, left_point_face: VDFace) -> tuple[list[VDFace], list[Optional[VDFace]]]:
        """Update the vertical decomposition with a given line_segment
        
        Returns both the now unvalid trapezoids and the newly created / changed trapezoids
        (a trapzoid may be in both lists)        
        """
        self.line_segments.append(line_segment)

        self._point_sequence.animate(PointReference([line_segment.left, line_segment.right], 0))

        # Find all other k intersected trapezoids (via neighbors) in O(k) time (see [1], page 130)
        intersected_trapezoids: list[VDFace] = []  # Does not include the left_point_face
        last_intersected = left_point_face
        while line_segment.right.horizontal_orientation(last_intersected.right_point) == HORT.RIGHT:  # ls extends to the right of the last added trapezoid
            if last_intersected.right_point.vertical_orientation(line_segment) == VORT.BELOW:  # Tests for vertical orientation is the same for the transformed instance using the shear transform phi
                last_intersected = last_intersected.upper_right_neighbor
            else:  # vertical_orientation == VORT.ABOVE, VORT.ON is impossible
                last_intersected = last_intersected.lower_right_neighbor

            intersected_trapezoids.append(last_intersected)
            
        if intersected_trapezoids == []:
            # Simple case: the "line_segment" is completely contained in the trapezoid "left_point_face"
            # The trapezoid is replaced by up to four new trapezoids (see [1], page 131)
            trapezoid_left, trapezoid_top, trapezoid_bottom, trapezoid_right = self._partition_trapezoid(left_point_face, line_segment)
            self._trapezoids.remove(left_point_face)
            self._trapezoids.extend(list(filter(None.__ne__, [trapezoid_left, trapezoid_top, trapezoid_bottom, trapezoid_right])))
            return [left_point_face], [trapezoid_left, trapezoid_top, trapezoid_bottom, trapezoid_right]

        # Other (more complicated) case: the "line_segment" intersects two or more trapezoids (Update in O(k) time)
        right_point_face = intersected_trapezoids.pop()
        
        # Partition the first and last trapezoid into three new trapezoids each
        upper_right, lower_right = left_point_face.upper_right_neighbor, left_point_face.lower_right_neighbor  # Retain pointers to the neighbors before any changes
        upper_left, lower_left = right_point_face.upper_left_neighbor, right_point_face.lower_left_neighbor

        # Partition the first trapezoid (containing the left endpoint)
        left_face, left_face_above, left_face_below, _ = self._partition_trapezoid(left_point_face, line_segment)
        self.trapezoids.remove(left_point_face)
        if left_face is not None:
            self.trapezoids.append(left_face)

        if left_point_face.right_point.vertical_orientation(line_segment) == VORT.ABOVE:  # Setting the top/bottom most neighbor
            left_face_above.upper_right_neighbor = upper_right
        elif left_point_face.right_point.vertical_orientation(line_segment) ==  VORT.BELOW:
            left_face_below.lower_right_neighbor = lower_right
        else:
            raise RuntimeError(f"Point {left_point_face.right_point} must not lie on line induced by the line segment {line_segment}")

        # Partition the last trapezoid (containing the right endpoint)
        _, right_face_above, right_face_below, right_face = self._partition_trapezoid(right_point_face, line_segment)
        self.trapezoids.remove(right_point_face)
        if right_face is not None:
            self.trapezoids.append(right_face)

        # Shorten vertical extensions that abut on the LS. => Merge trapezoids along the line-segment. (see [1], page 132)
        last_face_above, last_face_below = left_face_above, left_face_below
        for trapezoid in intersected_trapezoids:
            last_face_above, last_face_below = self._merge_trapezoids(trapezoid, line_segment, last_face_above, last_face_below)

        # Merge with (already split) last trapezoid
        self._point_sequence.animate(right_face_above.left_point)
        seq_point = self._point_sequence[right_face_above.left_point].copy()
        if right_face_above.left_point.vertical_orientation(line_segment) == VORT.ABOVE:  # point is the original leftp of right_point_face (equal in right_face_below)
            # Merge trapezoids below the LS and discard right_face_below
            last_face_below.right_point = line_segment.right
            last_face_below.lower_right_neighbor = right_face_below.lower_right_neighbor  # the right_point_face if the right endpoint of the linesegment is new and its old lower_right_neighbor otherwise
            last_face_below.upper_right_neighbor = None
            
            last_face_above.lower_right_neighbor = right_face_above  # Connect neighboring trapezoids above the LS
            right_face_above.upper_left_neighbor = upper_left  # Connect even higher neighbor
            kept_face = right_face_above
            if isinstance(seq_point, PointReference):
                seq_point.container[2] = Point(right_face_above.left_point.x, line_segment.y_from_x(right_face_above.left_point.x))
        elif right_face_above.left_point.vertical_orientation(line_segment) == VORT.BELOW:
            # Merge trapezoids above the LS and discard right_face_above
            last_face_above.right_point = line_segment.right
            last_face_above.lower_right_neighbor = None
            last_face_above.upper_right_neighbor = right_face_above.upper_right_neighbor
            
            last_face_below.upper_right_neighbor = right_face_below  # Connect neighboring trapezoids below the LS
            right_face_below.lower_left_neighbor = lower_left
            kept_face = right_face_below
            if isinstance(seq_point, PointReference):
                seq_point.container[1] = Point(right_face_above.left_point.x, line_segment.y_from_x(right_face_above.left_point.x))
        else:
            raise RuntimeError(f"Point {trapezoid.left_point} must not lie on line induced by the line segment {line_segment}")
        
        self._point_sequence[right_face_above.left_point] = seq_point
        
        self._trapezoids.extend([left_face_above, left_face_below, kept_face])
        return [left_point_face] + intersected_trapezoids + [right_point_face], [left_face, left_face_above, left_face_below, kept_face, right_face]

    def _partition_trapezoid(self, face: VDFace, line_segment: VDLineSegment) -> tuple[Optional[VDFace], VDFace, VDFace, Optional[VDFace]]:
        trapezoid_top = VDFace(face.top_line_segment, line_segment, line_segment.left, line_segment.right)
        trapezoid_bottom = VDFace(line_segment, face.bottom_line_segment, line_segment.left, line_segment.right)
        if (hort := line_segment.left.horizontal_orientation(face.left_point)) == HORT.LEFT:  # Case ls extends further to the left
            trapezoid_left = None
            trapezoid_top.left_point = face.left_point
            trapezoid_bottom.left_point = face.left_point
        elif hort == HORT.EQUAL:   # Case where the new linesegment shares an endpoint with an already existing endpoint
            trapezoid_left = None
            trapezoid_top.upper_left_neighbor = face.upper_left_neighbor
            trapezoid_bottom.lower_left_neighbor = face.lower_left_neighbor
            self._point_sequence.animate(line_segment.left)
        else:
            trapezoid_left = VDFace(face.top_line_segment, face.bottom_line_segment, face.left_point, line_segment.left)
            trapezoid_left.neighbors = [trapezoid_top, face.upper_left_neighbor, face.lower_left_neighbor, trapezoid_bottom]
            point_above = Point(line_segment.left.x, face.top_line_segment.y_from_x(line_segment.left.x))
            point_below = Point(line_segment.left.x, face.bottom_line_segment.y_from_x(line_segment.left.x))
            self._point_sequence.append(PointReference([line_segment.left, point_above.copy(), point_below.copy()], 0))  # For animations: copy(), because the values might change later.
        
        if (hort := line_segment.right.horizontal_orientation(face.right_point)) == HORT.RIGHT:
            trapezoid_right = None
            trapezoid_top.right_point = face.right_point
            trapezoid_bottom.right_point = face.right_point
        elif hort == HORT.EQUAL:
            trapezoid_right = None
            trapezoid_top.upper_right_neighbor = face.upper_right_neighbor
            trapezoid_bottom.lower_right_neighbor = face.lower_right_neighbor
            self._point_sequence.animate(line_segment.right)
        else:
            trapezoid_right = VDFace(face.top_line_segment, face.bottom_line_segment, line_segment.right, face.right_point)
            trapezoid_right.neighbors = [face.upper_right_neighbor, trapezoid_top, trapezoid_bottom, face.lower_right_neighbor]
            point_above = Point(line_segment.right.x, face.top_line_segment.y_from_x(line_segment.right.x))
            point_below = Point(line_segment.right.x, face.bottom_line_segment.y_from_x(line_segment.right.x))
            self._point_sequence.append(PointReference([line_segment.right, point_above.copy(), point_below.copy()], 0))

        return trapezoid_left, trapezoid_top, trapezoid_bottom, trapezoid_right
    
    def _merge_trapezoids(self, trapezoid: VDFace, line_segment: VDLineSegment, last_above: VDFace, last_below: VDFace):
        self._point_sequence.animate(trapezoid.left_point)
        seq_point = self._point_sequence[trapezoid.left_point].copy()
        if trapezoid.left_point.vertical_orientation(line_segment) == VORT.ABOVE:
            # Merge trapezoids below the LS
            if trapezoid.right_point.vertical_orientation(line_segment) == VORT.BELOW:  # Next one is on the other side, new neighbors are correct and final
                last_below.lower_right_neighbor = trapezoid.lower_right_neighbor
                last_below.upper_right_neighbor = trapezoid.upper_right_neighbor
            last_below.right_point = trapezoid.right_point

            # Shrink the intersected trapezoid to be above the LS
            trapezoid.bottom_line_segment = line_segment
            trapezoid.lower_left_neighbor = last_above
            last_above = trapezoid
            if isinstance(seq_point, PointReference):
                seq_point.container[2] = Point(trapezoid.left_point.x, line_segment.y_from_x(trapezoid.left_point.x))
        elif trapezoid.left_point.vertical_orientation(line_segment) == VORT.BELOW:
            # Merge trapezoids above the LS
            if trapezoid.right_point.vertical_orientation(line_segment) == VORT.ABOVE:
                last_above.lower_right_neighbor = trapezoid.lower_right_neighbor
                last_above.upper_right_neighbor = trapezoid.upper_right_neighbor
            last_above.right_point = trapezoid.right_point

            # Shrink the intersected trapezoid to be below the LS
            trapezoid.top_line_segment = line_segment
            trapezoid.upper_left_neighbor = last_below
            last_below = trapezoid
            if isinstance(seq_point, PointReference):
                seq_point.container[1] = Point(trapezoid.left_point.x, line_segment.y_from_x(trapezoid.left_point.x))
        else:
            raise RuntimeError(f"Point {trapezoid.left_point} must not lie on line induced by the line segment {line_segment}")
        self._point_sequence[trapezoid.left_point] = seq_point
        return last_above, last_below

            
class VDNode(ABC):
    __id = 0

    def __init__(self) -> None:
        self._left: Optional[VDNode] = None
        self._right: Optional[VDNode] = None
        self._parents: list[VDNode] = []  # The search structure is a DAG, hence a node can have multiple parents
        self._id = VDNode.__id
        VDNode.__id = VDNode.__id + 1
    
    # region properties

    @property
    def parents(self) -> list[VDNode]:
        return self._parents
    
    @property
    def parent(self) -> Optional[VDNode]:
        if self._parents == []:
            return None
        return self._parents[0]

    @parent.setter
    def parent(self, parent: Optional[VDNode]):
        if parent is None or parent in self._parents:
            return
        self._parents.append(parent)        

    # endregion

    def check_structure(self):
        if isinstance(self, VDLeaf):
            if self._left is not None or self._right is not None:
                raise RuntimeError(f"Leaf is not supposed to have children")
            if self._face is None:
                raise RuntimeError(f"Leaf {self} needs to have an associated trapezoid")
            if self._face.search_leaf is not self:
                raise RuntimeError(f"Wrong connection in Leaf {self} with the search leaf")
        
        if isinstance(self, VDXNode) and self._point is None:
            raise RuntimeError(f"X-Node needs to have a point")
        if isinstance(self, VDYNode) and self._line_segment is None:
            raise RuntimeError(f"Y-Nodes needs to have a LS")
        
        if isinstance(self, VDXNode) or isinstance(self, VDYNode):
            if self._left is None or self._right is None:
                raise RuntimeError(f"Inner node {self} is supposed to have children")
            if self not in self._left.parents:
                raise RuntimeError(f"Inner node {self} needs to be a parent of its left child")
            if self not in self._right.parents:
                raise RuntimeError(f"Inner node {self} needs to be a parent of its right child")
            self._left.check_structure()
            self._right.check_structure()


    @abstractmethod
    def search(self, point: Point, line_segment: Optional[VDLineSegment] = None, point_sequence = PointSequence()) -> VDFace:
        """Search/Query method for the search structure of the vertical decompostion.
        
        Parameters
        ----------
        point : Point
            The point to search (query) in the Vertical Decomposition
        line_segment : Optional[VDLineSegment]
            Used during insertion by a y-node when the searched point lies on the line-segment (=> shared left endpoint) to compare the slope of both line segments
        """
        pass

    def replace_with(self, new_node: VDNode) -> bool:
        if self._parents == []:  # node is the root
            return False
        for parent in self._parents:
            if parent._left is self:
                parent._left = new_node
            elif parent._right is self:
                parent._right = new_node
            else:
                raise Exception(f"{self} needs to be a child of its parent {parent}")
        
        new_node._parents = self._parents
        self._parents = []  
        return True
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__} with ID {self._id}"


class VDXNode(VDNode):
    def __init__(self, point: Point) -> None:
        super().__init__()
        self._point: Point = point

    # region properties

    @property
    def left(self) -> Optional[VDNode]:
        return self._left
    
    @left.setter
    def left(self, left: Optional[VDNode]):
        self._left = left
        if left != None:
            left.parent = self

    @property
    def right(self) -> Optional[VDNode]:
        return self._right
    
    @right.setter
    def right(self, right: Optional[VDNode]):
        self._right = right
        if right != None:
            right.parent = self

    # endregion

    def search(self, point: Point, line_segment: Optional[VDLineSegment] = None, point_sequence = PointSequence()) -> VDFace:
        point_sequence.append(self._point)
        if point.horizontal_orientation(self._point) == HORT.LEFT:  # Using symbolic shear transform
            return self._left.search(point, line_segment, point_sequence)
        else:  # The point lies to the right or coincides with the point of the node. Then we decide to continue to the right ([1], page 130 last paragraph). Durint insertion this results in a trapezoid of 0 width.
            return self._right.search(point, line_segment, point_sequence)


class VDYNode(VDNode):
    def __init__(self, line_segment: VDLineSegment) -> None:
        super().__init__()
        self._line_segment: VDLineSegment = line_segment

    # region properties

    @property
    def lower(self) -> Optional[VDNode]:
        return self._left
    
    @lower.setter
    def lower(self, lower: Optional[VDNode]):
        self._left = lower
        if lower != None:
            lower.parent = self

    @property
    def upper(self) -> Optional[VDNode]:
        return self._right
    
    @upper.setter
    def upper(self, upper: Optional[VDNode]):
        self._right = upper
        if upper != None:
            upper.parent = self

    # endregion

    def search(self, point: Point, line_segment: Optional[VDLineSegment] = None, point_sequence = PointSequence()) -> VDFace:
        point_sequence.append(PointReference([self._line_segment.left, self._line_segment.right], 0))
        cr = point.vertical_orientation(self._line_segment)

        # During insertion: cr == VORT.ON can only happen if the new line segment shares its left endpoint with the ls stored at this node
        if cr == VORT.ABOVE or (cr == VORT.ON and (line_segment is None or line_segment.slope() > self._line_segment.slope())):
            return self.upper.search(point, line_segment, point_sequence)
        elif cr == VORT.BELOW or (cr == VORT.ON and line_segment.slope() < self._line_segment.slope()):
            return self.lower.search(point, line_segment, point_sequence)
        else:
            raise AttributeError(f"The line segment {line_segment} cannot be inserted because it is already in the vertical decomposition")


class VDLeaf(VDNode):
    def __init__(self, face: VDFace) -> None:
        super().__init__()
        self._face: VDFace = face
        self._face.search_leaf = self

    def search(self, point: Point, line_segment: Optional[VDLineSegment] = None, point_sequence = PointSequence()) -> VDFace:
        return self._face


class VDSearchStructure(PLSearchStructure):
    def __init__(self, initial_face: VDFace) -> None:
        self._root: VDNode = VDLeaf(initial_face)

    # region properties

    @property
    def root(self) -> VDNode:
        return self._root
    
    # endregion

    def query(self, point: Point) -> tuple[Face, PointSequence]:
        point_sequence = PointSequence()
        point_sequence.append(point)
        vd_face = self._root.search(point, point_sequence=point_sequence)
        dcel_face = vd_face.bottom_line_segment.above_face
        
        point_sequence.clear()
        
        point_sequence.append(point)
        
        for vertex in dcel_face.outer_vertices():
            point_sequence.append(vertex.point)
        return dcel_face, point_sequence
    
    def update(self, line_segment: VDLineSegment, unvalid_leafs: list[Optional[VDLeaf]], new_leafs: list[Optional[VDLeaf]]):
        """Update the search structure using known leafs from updating the vertical decomposition"""
        if len(unvalid_leafs) == 1:  # Simple case: the "line_segment" is completely contained in the one trapezoid "left_point_face"
            tree = self._build_subtree(line_segment, new_leafs[0:4])

            success = unvalid_leafs[0].replace_with(tree)
            if not success:  # root element
                self._root = tree
            return
        
        # Other (more complicated) case: the line segment intersects two or more trapezoids.
        # Replace the leaf containing the left endpoint by a small tree composed of an x- and a y-node.
        left_endpoint_leaf = unvalid_leafs.pop(0)
        tree = self._build_subtree(line_segment, new_leafs[0:3])
        left_endpoint_leaf.replace_with(tree)  # checking for success is not necessary. The leaf node "left_endpoint_leaf" cannot be the root as there are >= 2 total unvalid leafs

        right_endpoint_leaf = unvalid_leafs.pop()  # leaf containing the right endpoint, filled after treatment of intersected trapezoids

        opposite_leaf = None  # leaf corresponding to the trapezoid on the other side of the LS
        if not unvalid_leafs == []:  # left and right point do not lie in directly neighboring faces
            # Init opposite_leaf: Either the leaf for left_face_above or left_face_below
            if unvalid_leafs[0]._face.bottom_line_segment is line_segment:
                opposite_leaf = new_leafs[2]
            else:
                opposite_leaf = new_leafs[1]
            opposite_leaf_orientation = opposite_leaf._face.right_point.vertical_orientation(line_segment)

            for i in range(0, len(unvalid_leafs)):  # Replace all unvalid leafs (beside first and last) by a single y-node
                tree = VDYNode(line_segment)
                unvalid_leafs[i].replace_with(tree)
                
                unvalid_leaf_orientation = unvalid_leafs[i]._face.left_point.vertical_orientation(line_segment)
                if unvalid_leaf_orientation == opposite_leaf_orientation:
                    opposite_leaf = unvalid_leafs[i-1]
                    opposite_leaf_orientation = opposite_leaf._face.left_point.vertical_orientation(line_segment)

                if unvalid_leaf_orientation == VORT.ABOVE:
                    tree.upper = unvalid_leafs[i]
                    tree.lower = opposite_leaf
                else:  # VORT.BELOW
                    tree.upper = opposite_leaf
                    tree.lower = unvalid_leafs[i]

            if new_leafs[-2]._face.left_point.vertical_orientation(line_segment) == opposite_leaf_orientation:
                opposite_leaf = unvalid_leafs[-1]  # Maintain opposite leaf one more time
        else:
            if new_leafs[-2]._face.bottom_line_segment is line_segment:
                opposite_leaf = new_leafs[2]
            else:
                opposite_leaf = new_leafs[1]

        # Replace the leaf containing the right endpoint        
        if new_leafs[-2]._face.bottom_line_segment is line_segment:  # kept_face is either right_face_above or right_face_below
            tree = self._build_subtree(line_segment, [None, new_leafs[-2], opposite_leaf, new_leafs[-1]])
        elif new_leafs[-2]._face.top_line_segment is line_segment:
            tree = self._build_subtree(line_segment, [None, opposite_leaf, new_leafs[-2], new_leafs[-1]])

        right_endpoint_leaf.replace_with(tree)

    def _build_subtree(self, line_segment: VDLineSegment, leafs: list[Optional[VDLeaf]]) -> VDNode:
        if len(leafs) < 3 or len(leafs) > 4:
            raise ValueError(f"The list of leafs {leafs} needs to be of length 3 or 4 to build a subtree.")
        # The leaf is replaced by a small tree composed of two x-nodes and a y-node
        tree = VDYNode(line_segment)
        tree.upper = leafs[1]
        tree.lower = leafs[2]
        if len(leafs) > 3 and leafs[3] is not None:  # The new line segment does not share an enpoint with an already existing endpoint
            child = tree
            tree = VDXNode(line_segment.right)
            tree.left = child
            tree.right = leafs[3]
        if leafs[0] is not None:
            child = tree
            tree = VDXNode(line_segment.left)
            tree.left = leafs[0]
            tree.right = child
        return tree


class VDFace:
    __id = 0

    def __init__(self, top_ls: VDLineSegment, bottom_ls: VDLineSegment, left_point: Point, right_point: Point) -> None:
        self._top_line_segment: VDLineSegment = top_ls
        self._bottom_line_segment: VDLineSegment = bottom_ls
        self._left_point: Point = left_point
        self._right_point: Point = right_point
        self._search_leaf: VDLeaf = None
        self._neighbors: list[VDFace] = [None, None, None, None]  # Up to four neighbors for each face
        self._id = VDFace.__id
        VDFace.__id = VDFace.__id + 1

    # region properties

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
    def neighbors(self, new_neighbors: list[Optional[VDFace]]):
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
    
    # endregion
            
    def __repr__(self) -> str:
        return f"ID: F{self._id} || Top-LS: {self._top_line_segment} | Bottom-LS: {self._bottom_line_segment} | Left-P: {self._left_point} | Right-P: {self._right_point}"

class VDLineSegment(LineSegment):
    def __init__(self, p: Point, q: Point):
        super().__init__(p, q)
        self._above_dcel_face: Optional[Face] = None  # The original face of the planar subdivision (DCEL)

    @classmethod
    def from_line_segment(cls, line_segment: LineSegment) -> VDLineSegment:
        return VDLineSegment(line_segment.left, line_segment.right)

    # region properties

    @property
    def above_face(self) -> Face:
        return self._above_dcel_face
    
    @above_face.setter
    def above_face(self, face: Face):
        self._above_dcel_face = face

    # endregion
