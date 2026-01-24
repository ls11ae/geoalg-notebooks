from __future__ import annotations

from typing import override, Callable
from .base import Node, BinaryTree, K, V, A, TreeTracker
from ...geometry import Comparator, ComparisonResult
"""
implementation of a binary search tree
"""

class BSTNode(Node[K, V]):
    def __init__(self, key: K, value: V):
        super().__init__(key, value)

    @override
    def insert(self, key: K, value: V, comparator: Comparator[K], auto_balance : bool) -> bool:
        cr = comparator.compare(key, self._key)
        if cr == ComparisonResult.BEFORE:
            if self._left is None:
                self._update_left(BSTNode(key, value))
                self._update_after_insert(auto_balance)
                return True
            else:
                return self._left.insert(key, value, comparator, auto_balance)
        elif cr == ComparisonResult.AFTER:
            if self._right is None:
                self._update_right(BSTNode(key, value))
                self._update_after_insert(auto_balance)
                return True
            else:
                return self._right.insert(key, value, comparator, auto_balance)
        else:
            return False

    @override
    def delete(self, key: K, comparator: Comparator[K]) -> bool:
        raise NotImplementedError()

    @override
    def less_or_equal(self, upper_bound: K, comparator: Comparator[K], tracker : TreeTracker, f: Callable[[Node[K, V]], A]) -> list[A]:
        raise NotImplementedError

    @override
    def greater_or_equal(self, lower_bound: K, comparator: Comparator[K], tracker : TreeTracker, f: Callable[[Node[K, V]], A]) -> list[A]:
        raise NotImplementedError

class BST(BinaryTree[K]):
    """Binary search tree"""
    def __init__(self, comparator: Comparator[K], auto_balance: bool):
        super().__init__(comparator, auto_balance)

    @override
    def insert(self, key: K) -> bool:
        if self._root is None:
            self._root = BSTNode(key, None)
            return True
        return super().insert(key)