from __future__ import annotations

from typing import Generic, Optional, override, List, Tuple
from .base import Node, BinaryTree, Comparator, ComparisonResult, K, V

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
                self.left = BSTNode(key, value)
                self._update_after_insert(auto_balance)
                return True
            else:
                return self._left.insert(key, value, comparator, auto_balance)
        elif cr == ComparisonResult.AFTER:
            if self._right is None:
                self.right = BSTNode(key, value)
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
    def path(self, key: K, comparator: Comparator[K]) -> list[Node[K, V]]:
        pass

class BST(BinaryTree[K]):
    """Binary search tree"""
    def __init__(self, comparator: Comparator[K], auto_balance: bool):
        super().__init__(comparator, auto_balance)

    @override
    def insert(self, key: K) -> bool:
        if self._root is None:
            self._root = BSTNode(key, None)
            return True
        if self._root.insert(key, None, self._comparator, self._auto_balance):
            self._root = self._root.root
            return True
        return False