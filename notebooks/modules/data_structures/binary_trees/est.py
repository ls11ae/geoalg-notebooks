from __future__ import annotations
from typing import override, Callable
from .base import Node, BinaryTree, K, V, A, TreeTracker
from ...geometry import Comparator, ComparisonResult


class ESTNode(Node[K, V]):
    """
    Implementation of an external search tree. Keys are repeated more than once such that every appears in the leaves
    exactly once. This ensures every node has either 0 or 2 children
    """
    def __init__(self, key: K, value: V):
        super().__init__(key, value)

    @override
    def insert(self, key: K, value: V, comparator: Comparator[K], auto_balance : bool) -> bool:
        cr = comparator.compare(key, self._key)
        if cr == ComparisonResult.BEFORE or cr == ComparisonResult.MATCH:
            if self.is_leaf():
                self._update_left(ESTNode(key, value))
                self._update_right(ESTNode(self._key, self._value))
                self._key = key
                self._value = value
                self._update_after_insert(auto_balance)
                return True
            else:
                return self._left.insert(key, value, comparator, auto_balance)
        elif cr == ComparisonResult.AFTER:
            if self.is_leaf():
                self._update_left(ESTNode(self._key, self._value))
                self._update_right(ESTNode(key, value))
                self._key = key
                self._value = value
                self._update_after_insert(auto_balance)
                return True
            else:
                return self._right.insert(key, value, comparator, auto_balance)
        else:
            return False

    @override
    def less_or_equal(self, upper_bound : K, comparator : Comparator[K], tracker : TreeTracker[V,K], f : Callable[[Node[K,V]], A]) -> list[A]:
        tracker.track_node_visit(self)
        cr = comparator.compare(upper_bound, self._key)
        if cr is ComparisonResult.MATCH or cr is ComparisonResult.AFTER:
            #less than search term
            if not self.is_leaf():
                tracker.track_method_call("leaves")
                result_left = self._left.leaves(tracker, f)
                tracker.track_node_visit(self)
                result_right = self._right.less_or_equal(upper_bound, comparator, tracker, f)
                tracker.track_node_visit(self)
                return result_left + result_right
            else:
                result = [f(self)]
                tracker.track_partial_result(result)
                return result
        else:
            #more than search term
            if not self.is_leaf():
                result = self._left.less_or_equal(upper_bound, comparator, tracker, f)
                tracker.track_node_visit(self)
                return result
            else:
                return []

    @override
    def greater_or_equal(self, lower_bound : K, comparator : Comparator[K], tracker : TreeTracker[V,K], f : Callable[[Node[K,V]], A]) -> list[A]:
        tracker.track_node_visit(self)
        cr = comparator.compare(lower_bound, self._key)
        if cr is ComparisonResult.BEFORE or cr is ComparisonResult.MATCH:
            #more than or equal  to search term
            if not self.is_leaf():
                result_left = self._left.greater_or_equal(lower_bound, comparator, tracker, f)
                tracker.track_node_visit(self)
                tracker.track_method_call("leaves")
                result_right = self._right.leaves(tracker, f)
                tracker.track_node_visit(self)
                return result_left + result_right
            else:
                result = [f(self)]
                tracker.track_partial_result(result)
                return result
        else:
            #more than search term
            if not self.is_leaf():
                result = self._right.greater_or_equal(lower_bound, comparator, tracker, f)
                tracker.track_node_visit(self)
                return result
            else:
                return []


    @override
    def delete(self, key: K, comparator: Comparator[K]) -> bool:
        raise NotImplementedError()

class EST(BinaryTree[K]):
    """external search tree"""
    def __init__(self, comparator : Comparator[K], auto_balance : bool):
        super().__init__(comparator, auto_balance)

    @override
    def insert(self, key: K) -> bool:
        if self._root is None:
            self._root = ESTNode(key, None)
            return True
        return super().insert(key)