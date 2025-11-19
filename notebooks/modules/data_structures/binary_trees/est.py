from __future__ import annotations
from typing import Generic, Optional, override, List, Tuple
from .base import Node, BinaryTree, Comparator, ComparisonResult, K, V

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
                self.left = ESTNode(key, value)
                self.right = ESTNode(self._key, self._value)
                self._key = key
                self._value = value
                self._update_after_insert(auto_balance)
                return True
            else:
                return self._left.insert(key, value, comparator, auto_balance)
        elif cr == ComparisonResult.AFTER:
            if self.is_leaf():
                self.left = ESTNode(self._key, self._value)
                self.right = ESTNode(key, value)
                self._key = key
                self._value = value
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
    def path(self, key : K, comparator : Comparator[K]) -> list[Node[K, V]]:
        pass

class EST(BinaryTree[K]):
    """external search tree"""
    def __init__(self, comparator: Comparator[K], auto_balance: bool):
        super().__init__(comparator, auto_balance)

    @override
    def insert(self, key: K) -> bool:
        if self._root is None:
            self._root = ESTNode(key, None)
            self._root = self._root.root
            return True
        return self._root.insert(key, None, self._comparator, self._auto_balance)