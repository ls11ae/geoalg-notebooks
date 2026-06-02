from collections import deque

from ..geometry import Point
from ..data_structures import RangeTreeAnimator
from typing import Optional


class YNode:
    def __init__(self):
        self.point : Optional[Point] = None
        self.left : Optional[YNode] = None
        self.right : Optional[YNode] = None
        self.parent : Optional[YNode] = None

    def level_order(self):
        if self is None:
            return
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)

class XNode:
    def __init__(self):
        self.point : Optional[Point] = None
        self.y_root : Optional[YNode] = None
        self.left : Optional[XNode] = None
        self.right : Optional[XNode] = None
        self.parent : Optional[XNode] = None

    def level_order(self):
        if self is None:
            return
        queue = deque([self])
        while queue:
            node = queue.popleft()
            yield node
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)

def y_leaves(node : YNode, rta : RangeTreeAnimator) -> list[Point]:
    if node.left is None and node.right is None:
        rta.tag_cur_y(1)
        #print("leaves: " + str(rta._cur_y) + ", " + str(node.point))
        return [node.point]
    else:
        rta.tag_cur_y(2)
        rta.go_to_left_child_y()
        left_leaves = y_leaves(node.left, rta)
        rta.go_to_parent_y()
        rta.go_to_right_child_y()
        right_leaves = y_leaves(node.right, rta)
        rta.go_to_parent_y()
        rta.tag_cur_y(0)
        return left_leaves + right_leaves

def y_less_or_equal(node : YNode, upper_bound : int, rta : RangeTreeAnimator) -> list[Point]:
    if node.point.y <= upper_bound:
        #less than search term
        if node.left is not None and node.right is not None:
            rta.tag_cur_y(2)
            rta.go_to_left_child_y()
            left_result = y_leaves(node.left, rta)
            rta.go_to_parent_y()
            rta.go_to_right_child_y()
            right_result = y_less_or_equal(node.right, upper_bound, rta)
            rta.go_to_parent_y()
            rta.tag_cur_y(0)
            return left_result + right_result
        else:
            rta.tag_cur_y(1)
            #print("y_less_or_equal: " + str(rta._cur_y) + ", " + str(node.point))
            return [node.point]
    else:
        #more than search term
        if not node.left is None:
            rta.tag_cur_y(2)
            rta.go_to_left_child_y()
            left_result = y_less_or_equal(node.left, upper_bound, rta)
            rta.go_to_parent_y()
            rta.tag_cur_y(0)
            return left_result
        else:
            rta.tag_cur_y(3)
            return []

def y_greater_or_equal(node : YNode, lower_bound : int, rta : RangeTreeAnimator) -> list[Point]:
    if node.point.y >= lower_bound:
        #more than search term
        if node.left is not None and node.right is not None:
            rta.tag_cur_y(2)
            rta.go_to_left_child_y()
            left_result = y_greater_or_equal(node.left, lower_bound, rta)
            rta.go_to_parent_y()
            rta.go_to_right_child_y()
            right_result = y_leaves(node.right, rta)
            rta.go_to_parent_y()
            rta.tag_cur_y(0)
            return left_result + right_result
        else:
            rta.tag_cur_y(1)
            #print("y_greater_or_equal: " + str(rta._cur_y) + ", " + str(node.point))
            return [node.point]
    else:
        #less than search term
        if node.right is not None:
            rta.tag_cur_y(2)
            rta.go_to_right_child_y()
            right_result = y_greater_or_equal(node.right, lower_bound, rta)
            rta.go_to_parent_y()
            rta.tag_cur_y(0)
            return right_result
        else:
            rta.tag_cur_y(3)
            return []

def y_find_splitting_node(node : YNode, lower_bound : int, upper_bound : int, rta : RangeTreeAnimator) -> Optional[YNode]:
    if node.point.y > upper_bound:
        if node.left is None:
            return None
        else:
            rta.go_to_left_child_y()
            split_node = y_find_splitting_node(node.left, lower_bound,upper_bound, rta)
            rta.go_to_parent_y()
            return split_node
    elif node.point.y < lower_bound:
        if node.right is None:
            return None
        else:
            rta.go_to_right_child_y()
            split_node = y_find_splitting_node(node.right, lower_bound,upper_bound, rta)
            rta.go_to_parent_y()
            return split_node
    else:
        return node

def y_range_search(node: YNode, lower_bound: int, upper_bound: int, rta: RangeTreeAnimator) -> list[Point]:
    splitting_node = y_find_splitting_node(node, lower_bound, upper_bound, rta)
    if splitting_node is None:
        return []
    if splitting_node.left is None and splitting_node.right is None:
        rta.tag_cur_y(1)
        return [splitting_node.point]
    else:
        result = []
        if splitting_node.left is not None:
            rta.go_to_left_child_y()
            result += y_greater_or_equal(splitting_node.left, lower_bound, rta)
            rta.go_to_parent_y()
        if splitting_node.right is not None:
            rta.go_to_right_child_y()
            result += y_less_or_equal(splitting_node.right, upper_bound, rta)
            rta.go_to_parent_y()
        return result

def x_find_splitting_node(node : XNode, lower_bound : int, upper_bound : int, rta : RangeTreeAnimator) -> Optional[XNode]:
    if node.point.x > upper_bound:
        if node.left is None:
            return None
        else:
            rta.go_to_left_child_x()
            split_node = x_find_splitting_node(node.left, lower_bound,upper_bound, rta)
            rta.go_to_parent_x()
            return split_node
    elif node.point.x < lower_bound:
        if node.right is None:
            return None
        else:
            rta.go_to_right_child_x()
            split_node = x_find_splitting_node(node.right, lower_bound,upper_bound, rta)
            rta.go_to_parent_x()
            return split_node
    else:
        return node