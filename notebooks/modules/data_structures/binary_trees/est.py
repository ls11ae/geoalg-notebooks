from __future__ import annotations
from typing import Optional, override
from .base import Node, BinaryTree, K, V
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

    def range_query(self, r : tuple[K,K]) -> list[Node[K, V]]:
        leaves = []
        split_node = self._find_split_node(r)
        if split_node is None:
            return leaves
        left_path = split_node.left.path_to_leaf(r[0], self._comparator)
        right_path = split_node.right.path_to_leaf(r[1], self._comparator)
        for node in left_path:
            if node.is_leaf():
                cr_left = self._comparator.compare(node.key, r[0])
                cr_right = self._comparator.compare(node.key, r[1])
                if (cr_left == ComparisonResult.BEFORE or cr_left == ComparisonResult.MATCH) and (cr_right == ComparisonResult.BEFORE or cr_right == ComparisonResult.MATCH):
                    leaves.append(node)
            else:
                if node.right is not None:
                    leaves.extend(node.right.leaves())
        for node in right_path:
            if node.is_leaf():
                cr_left = self._comparator.compare(node.key, r[0])
                cr_right = self._comparator.compare(node.key, r[1])
                if (cr_left == ComparisonResult.BEFORE or cr_left == ComparisonResult.MATCH) and (cr_right == ComparisonResult.BEFORE or cr_right == ComparisonResult.MATCH):
                    leaves.append(node)
            else:
                if node.left is not None:
                    leaves.extend(node.left.leaves())
        return leaves

    def _find_split_node(self, r : tuple[K,K]) -> Optional[Node[K, None]]:
        if self._root is None:
            return None
        node = self._root
        while node is not None and not node.is_leaf():
            cr_left = self._comparator.compare(r[0], node.key)
            cr_right = self._comparator.compare(r[1], node.key)
            if cr_right is ComparisonResult.BEFORE or cr_right is ComparisonResult.MATCH:
                node = node.left #range fully left of node
            elif cr_left is ComparisonResult.AFTER:
                node = node.right #range fully right of node
            else:
                return node #node within the range
        return node