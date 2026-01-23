from __future__ import annotations
from typing import Generic, Optional, Callable
from abc import ABC, abstractmethod

from .node import Node, TreeTracker, K, V, A
from ....geometry import Comparator


class BinaryTree(Generic[K], ABC):
    """
    Abstract binary search tree, for implementation see BST and EST.

    Note: methods often take an optional parameter f : Callable[[Node[K,V]], A]. This parameter is used to transform the
    nodes returned into another datatype. If f is not given to the method as a parameter, it defaults do transforming
    every node into its key.

    Attributes
    ----------
    _root : Optional[Node[K, None]]
        root of the tree
    _comparator : Comparator[K]
        a way to compare to keys
    _auto_balance : bool
        if the tree should automatically balance after insertions and deletions.
    """

    def __init__(self, comparator: Comparator[K], auto_balance: bool):
        self._root: Optional[Node[K, None]] = None
        self._comparator = comparator
        self._auto_balance = auto_balance

    def insert(self, key: K) -> bool:
        if self._root is None:
            raise NotImplementedError  # this class cannot create nodes itself as the base node class is abstract
        if self._root.insert(key, None, self._comparator, self._auto_balance):
            self._root = self._root.root  #update root in case of rotations
            return True
        return False

    def delete(self, key: K) -> bool:
        if self._root is None:
            return False
        return self._root.delete(key, self._comparator)

    def pre_order(self, f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[A]:
        if self._root is None:
            return []
        return self._root.pre_order(f)

    def post_order(self, f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[A]:
        if self._root is None:
            return []
        return self._root.post_order(f)

    def in_order(self, f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[A]:
        if self._root is None:
            return []
        return self._root.in_order(f)

    def leaves(self, tracker: TreeTracker[K, V], f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[A]:
        if tracker is None:
            tracker = TreeTracker()
        tracker.track_method_call(self.leaves.__name__)
        if self._root is None:
            return tracker.track_method_return([])
        return tracker.track_method_return(self._root.leaves(tracker, f))

    def level_order(self, f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[list[A]]:
        """
        Returns a list containing each level of the tree as a list. Missing entries are filled None so the
        size of the outer list is always 2^tree_size.

        Parameters
        ----------
        f : Callable[[Node[K,V]], A]
            transforms node
        """
        if self._root is None:
            return []
        levels: list[list[A]] = []
        for i in range(0, self._root.level + 1):
            levels.append([])
        self._root.level_order(levels, f, 0, self._root.level)
        return levels

    def leq(self, upper_bound: K, tracker: TreeTracker[K, V], f: Callable[[Node[K, V]], A] = lambda n: n.key) -> \
    list[A]:
        """
        Returns all nodes that are less than or equal to upper_bound
        """
        if tracker is None:
            tracker = TreeTracker()
        tracker.track_method_call(self.leq.__name__)
        if self._root is None:
            return tracker.track_method_return([])
        return tracker.track_method_return(self._root.leq(upper_bound, self._comparator, tracker, f))

    def geq(self, lower_bound: K, tracker: TreeTracker[K, V], f: Callable[[Node[K, V]], A] = lambda n: n.key) -> \
    list[A]:
        """
        Returns all nodes that are greater than or equal to lower_bound
        """
        if tracker is None:
            tracker = TreeTracker()
        tracker.track_method_call(self.geq.__name__)
        if self._root is None:
            return tracker.track_method_return([])
        return tracker.track_method_return(self._root.geq(lower_bound, self._comparator, tracker, f))

    def first_in_range(self, lower_bound: K, upper_bound: K, tracker: TreeTracker[K, V],
                       f: Callable[[Node[K, V]], A] = lambda n: n.key) -> Node[K, V] | None:
        if tracker is None:
            tracker = TreeTracker()
        tracker.track_method_call(self.first_in_range.__name__)
        if self._root is None:
            return tracker.track_method_return(None)
        return tracker.track_method_return(self._root.first_in_range(lower_bound, upper_bound, self._comparator, tracker, f))

    def in_range(self, lower_bound: K, upper_bound: K, tracker: TreeTracker[K, V],
                 f: Callable[[Node[K, V]], A] = lambda n: n.key) -> list[A]:
        if tracker is None:
            tracker = TreeTracker()
        tracker.track_method_call(self.in_range.__name__)
        if self._root is None:
            return tracker.track_method_return([])
        splitting_node = self.first_in_range(lower_bound, upper_bound, tracker, lambda n: n)
        if splitting_node is None:
            return tracker.track_method_return([])
        if splitting_node.is_leaf():
            return tracker.track_method_return([f(splitting_node)])
        else:
            result = []
            if splitting_node.left is not None:
                tracker.track_method_call(splitting_node.left.geq.__name__)
                result += tracker.track_method_return(splitting_node.left.geq(lower_bound, self._comparator, tracker, f))
            if splitting_node.right is not None:
                tracker.track_method_call(splitting_node.left.leq.__name__)
                result += tracker.track_method_return(splitting_node.right.leq(upper_bound, self._comparator, tracker, f))
            return tracker.track_method_return(result)

    @property
    def comparator(self) -> Comparator[K]:
        return self._comparator

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
