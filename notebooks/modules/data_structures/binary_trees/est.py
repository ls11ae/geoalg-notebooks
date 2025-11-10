from __future__ import annotations
from typing import Generic, Optional, override, List, Tuple
from .base import Node, Comparator, ComparisonResult, K, V

"""
Implementation of an external search tree. All data is stored in the leaves
"""

class ESTNode(Node[K, V]):
    def __init__(self, key: K, value: V):
        super().__init__(key, value)

    @override
    def insert(self, key: K, value: V, comparator: Comparator[K]) -> bool:
        cr = comparator.compare(key, self._value)
        if cr == ComparisonResult.BEFORE or cr == ComparisonResult.MATCH:
            # Note: every node that isn't a leaf has exactly 2 children
            if self.is_leaf():
                self.left = ESTNode(key, value)
                self.right = ESTNode(self._key, self._value)
                self.level = 1
                return True
            else:
                return self._left.insert(key, value, comparator)
        elif cr == ComparisonResult.AFTER:
            if self.is_leaf():
                self.left = ESTNode(self._key, self._value)
                self.right = ESTNode(key, value)
                self.level = 1
                return True
            else:
                return self._right.insert(key, value, comparator)
        else:
            return False

    @override
    def delete(self, key: K, comparator: Comparator[K]) -> bool:
        raise NotImplementedError()

class EST(Generic[K]):
    """external search tree"""
    def __init__(self, comparator: Comparator[K]):
        self._root : Optional[ESTNode[K, None]] = None
        self._comparator = comparator

    def insert(self, key: K) -> bool:
        if self._root is None:
            self._root = ESTNode(key, None)
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