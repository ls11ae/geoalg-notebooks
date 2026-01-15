from __future__ import annotations
from typing import Generic, Optional, Callable
from abc import ABC, abstractmethod

from .node import Node, TreeTracker, K, V, A
from ....geometry import Comparator


class BinaryTree(Generic[K], ABC):
    """Binary search tree"""
    def __init__(self, comparator: Comparator[K], auto_balance : bool):
        self._root : Optional[Node[K, None]] = None
        self._comparator = comparator
        self._auto_balance = auto_balance
    @abstractmethod
    def insert(self, key: K) -> bool:
        pass

    def delete(self, key : K) -> bool:
        if self._root is not None:
            return self._root.delete(key, self._comparator)
        return False

    def pre_order(self, f : Callable[[Node[K,V]], A] = lambda n : n.key) -> list[A]:
        """
        Returns the tree in pre-order. Instead of returning the nodes directly, each is instead passed through f.

        Parameters
        ----------
        f : Callable[[Node[K,V]], A]
            transforms node
        """
        if self._root is not None:
            return self._root.pre_order(f)
        return []

    def post_order(self, f : Callable[[Node[K,V]], A] = lambda n : n.key) -> list[A]:
        """
        Returns the tree in post-order. Instead of returning the nodes directly, each is instead passed through f.

        Parameters
        ----------
        f : Callable[[Node[K,V]], A]
            transforms node
        """
        if self._root is not None:
            return self._root.post_order(f)
        return []

    def in_order(self, f : Callable[[Node[K,V]], A] = lambda n : n.key) -> list[A]:
        """
        Returns the tree in in-order. Instead of returning the nodes directly, each is instead passed through f.

        Parameters
        ----------
        f : Callable[[Node[K,V]], A]
            transforms node
        """
        if self._root is not None:
            return self._root.in_order(f)
        return []

    def leaves(self, f : Callable[[Node[K,V]], A] = lambda n : n.key) -> list[A]:
        """
        Returns the leaves of the tree. Instead of returning the nodes directly, each is instead passed through f.

        Parameters
        ----------
        f : Callable[[Node[K,V]], A]
            transforms node
        """
        if self._root is not None:
            return self._root.leaves(f)
        return []

    def level_order(self, f : Callable[[Node[K,V]], A] = lambda n : n.key) -> list[list[A]]:
        """
        Returns a list containing each level of the tree in a list. Missing entries are filled None so the
        size of the outer list is always 2^size.
        Each Node is transformed by f before being added to the list

        Parameters
        ----------
        f : Callable[[Node[K,V]], A]
            transforms node
        """
        if self._root is None:
            return []
        levels : list[list[A]] = []
        for i in range(0, self._root.level + 1):
            levels.append([])
        self._root.level_order(levels, f, 0, self._root.level)
        return levels

    def first_in_range(self, lower_bound : K, upper_bound : K, tracker : TreeTracker[K,V], f: Callable[[Node[K, V]], A] = lambda n: n.key) -> Node[K,V] | None:
        if self._root is None:
            return None
        if tracker is None:
            tracker = TreeTracker()
        return self._root.first_in_range(lower_bound, upper_bound, self._comparator, tracker, f)

    def report_leq(self, upper_bound: K, f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[A]:
        if self._root is None:
            return []
        return self._root.report_leq(upper_bound, self._comparator, f)

    def report_geq(self, lower_bound: K, f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[A]:
        if self._root is None:
            return []
        return self._root.report_geq(lower_bound, self._comparator, f)

    def report_in_range(self, lower_bound: K, upper_bound: K, f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[A]:
        if self._root is None:
            return []
        splitting_node = self._root.first_in_range(lower_bound, upper_bound, self._comparator, TreeTracker(), lambda n: n)
        if splitting_node is None:
            return []
        if splitting_node.is_leaf():
            return [splitting_node]
        else:
            ret = []
            if splitting_node.left is not None:
                ret += splitting_node.left.report_geq(lower_bound, self._comparator, f)
            if splitting_node.right is not None:
                ret += splitting_node.right.report_leq(upper_bound, self._comparator, f)
            return ret


    @property
    def comparator(self) -> Comparator[K]:
        return self._comparator

    @comparator.setter
    def comparator(self, comparator: Comparator[K]):
        self._comparator = comparator

    @property
    def size(self) -> int:
        if self._root is None:
            return 0
        else:
            return self._root.size

    @property
    def height(self) -> int:
        if self._root is None:
            return 0
        else:
            return self._root.level

    def draw(self):
        pass