from __future__ import annotations
from typing import Generic, Optional, override, List, Tuple
from .base import Node, Comparator, ComparisonResult, K, V

"""
implementation of a binary search tree
"""

class BSTNode(Node[K, V]):
    def __init__(self, key: K, value: V):
        super().__init__(key, value)

    @override
    def insert(self, key: K, value: V, comparator: Comparator[K]) -> bool:
        cr = comparator.compare(key, self._value)
        if cr == ComparisonResult.BEFORE:
            if self._left is None:
                self.left = BSTNode(key, value)
                self.level = max(1, self._level)
                return True
            else:
                return self._left.insert(key, value, comparator)
        elif cr == ComparisonResult.AFTER:
            if self._right is None:
                self.right = BSTNode(key, value)
                self.level = max(self._level, 1)
                return True
            else:
                return self._right.insert(key, value, comparator)
        else:
            return False

    @override
    def delete(self, key: K, comparator: Comparator[K]) -> bool:
        raise NotImplementedError()

class BST(Generic[K]):
    """Binary search tree"""
    def __init__(self, comparator: Comparator[K]):
        self._root : Optional[BSTNode[K, None]] = None
        self._comparator = comparator

    def insert(self, key: K) -> bool:
        if self._root is None:
            self._root = BSTNode(key, None)
            return True
        return self._root.insert(key, None, self._comparator)

    def delete(self, key : K):
        raise NotImplementedError()

    @property
    def comparator(self) -> Comparator[K]:
        return self._comparator

    @comparator.setter
    def comparator(self, comparator: Comparator[K]):
        self._comparator = comparator