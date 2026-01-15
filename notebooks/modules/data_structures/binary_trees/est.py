from __future__ import annotations
from typing import override, Callable
from .base import Node, BinaryTree, K, V, A
from ...geometry import Comparator, ComparisonResult

"""
Implementation of an external search tree. All data is stored in the leaves
"""

class ESTNode(Node[K, V]):
    def __init__(self, key: K, value: V):
        super().__init__(key, value)

    @override
    def insert(self, key: K, value: V, comparator: Comparator[K], auto_balance : bool) -> bool:
        cr = comparator.compare(key, self._key)
        if cr == ComparisonResult.BEFORE or cr == ComparisonResult.MATCH:
            # Note: every node that isn't a leaf has exactly 2 children
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
    def report_leq(self, upper_bound : K, comparator : Comparator[K], f : Callable[[Node[K,V]], A]) -> list[A]:
        cr = comparator.compare(upper_bound, self._key)
        if cr is ComparisonResult.MATCH or cr is ComparisonResult.AFTER:
            #less than search term
            if not self.is_leaf():
                return self._left.leaves(f) + self._right.report_leq(upper_bound, comparator, f)
            else:
                return [f(self)]
        else:
            #more than search term
            if not self.is_leaf():
                return self._left.report_leq(upper_bound, comparator, f)
            else:
                return []

    @override
    def report_geq(self, upper_bound : K, comparator : Comparator[K], f : Callable[[Node[K,V]], A]) -> list[A]:
        cr = comparator.compare(upper_bound, self._key)
        if cr is ComparisonResult.BEFORE or cr is ComparisonResult.MATCH:
            #less than search term
            if not self.is_leaf():
                return  self._left.report_geq(upper_bound, comparator, f) + self._right.leaves(f)
            else:
                return [f(self)]
        else:
            #more than search term
            if not self.is_leaf():
                return self._right.report_geq(upper_bound, comparator, f)
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
        if self._root.insert(key, None, self._comparator, self._auto_balance):
            self._root = self._root.root
            return True
        return False