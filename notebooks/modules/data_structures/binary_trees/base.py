from __future__ import annotations
from typing import TypeVar, Generic, Optional, List, Callable
from abc import ABC, abstractmethod

from prompt_toolkit.filters import control_is_searchable

from ...geometry import Comparator, ComparisonResult

'''Note: compared to the other implementation in data_structures.binary_tree.py this one is more generalized, but lacks
    a lot of functionality. If the missing methods are added, remember to generalize the use of PointSequence to AnimationObject'''

K = TypeVar("K")
V = TypeVar("V")

A = TypeVar("A")

class Node(Generic[K, V], ABC):
    """Abstract node that implements a tree structure.

    Attributes
    ----------
    _key : K
        key used for comparisons when searching in the tree
    _value : V
        value of the node
    _left : Optional[Node[K, V]]
        left child
    _right : Optional[Node[K, V]]
        right child
    _parent : Optional[Node[K, V]]
        parent node
    _level : int
        level of the Node in a tree, 0 = leaf, 1+ = inner node

    Methods
    -------
    is_empty()
        true if key is None, false otherwise
    is_leaf()
        true if the node is a leaf (level = 1), false otherwise
    insert(key: K, value: V, comparator: Comparator[K])
        insert new data
    delete(key: K, comparator: Comparator[K])
        delete data
    """

    def __init__(self, key: K, value: V):
        self._key : K = key
        self._value : V = value
        self._left : Optional[Node[K,V]] = None
        self._right : Optional[Node[K,V]] = None
        self._parent : Optional[Node[K,V]] = None
        self._level : int = 0
        self._balance : int = 0
        self._size : int = 1

    def is_leaf(self) -> bool:
        return self._left is None and self._right is None

    def is_root(self) -> bool:
        return self._parent is None

    @abstractmethod
    def insert(self, key: K, value: V, comparator : Comparator[K], auto_balance: bool) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key : K , comparator : Comparator[K]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def report_leq(self, upper_bound: K, comparator: Comparator[K], f: Callable[[Node[K, V]], A]) -> list[A]:
        raise NotImplementedError

    @abstractmethod
    def report_geq(self, lower_bound: K, comparator: Comparator[K], f: Callable[[Node[K, V]], A]) -> list[A]:
        raise NotImplementedError

    def pre_order(self, f : Callable[[Node[K,V]], A]) -> list[A]:
        return ([f(self)] +
                ([None] if self._left is None else (self._left.pre_order(f))) +
                ([None] if self._right is None else self._right.pre_order(f)))

    def post_order(self, f : Callable[[Node[K,V]], A]) -> list[A]:
        return (([None] if self._left is None else self._left.post_order(f)) +
                ([None] if self._right is None else self._right.post_order(f)) +
                [f(self)])

    def in_order(self, f : Callable[[Node[K,V]], A]) -> list[A]:
        return (([None] if self._left is None else self._left.in_order(f)) +
                [f(self)] +
                ([None] if self._right is None else self._right.in_order(f)))

    def leaves(self, f : Callable[[Node[K,V]], A]) -> list[A]:
        if self.is_leaf():
            return [f(self)]
        return (([] if self._left is None else self._left.leaves(f)) +
                ([] if self._right is None else self._right.leaves(f)))

    def level_order(self, levels : list[list[A]], f : Callable[[Node[K,V]], A], depth : int,  root_level : int):
        """
        Returns a list containing each level of the tree in a list. Missing entries are filled None so the
        size of the outer list is always 2^size.
        Each Node is transformed by f before being added to the list

        Parameters
        ----------
        levels : list[list[A]]

        f : Callable[[Node[K,V]], A]
            transforms node
        depth : int
            how far down from the root the current node is
        root_level : int
            level of the root/total height of the tree

        """
        cur_level = root_level - depth #level of the node assuming a full tree
        levels[depth].append(f(self))
        if self._left is not None:
            self._left.level_order(levels, f, depth + 1, root_level)
        else:
            for i in range(0, cur_level):
                for j in range(0, 2**i):
                    levels[i+depth+1].append(None)
        if self._right is not None:
            self._right.level_order(levels, f, depth + 1, root_level)
        else:
            for i in range(0, cur_level):
                for j in range(0, 2**i):
                    levels[i + depth + 1].append(None)

    def first_in_range(self, lower_bound: K, upper_bound: K, comparator : Comparator[K], f : Callable[[Node[K,V]], A]) -> A | None:
        cr_left = comparator.compare(lower_bound, self._key)
        cr_right = comparator.compare(upper_bound, self._key)
        if cr_right is ComparisonResult.BEFORE:
            #range fully left of node
            if self._left is None:
                return None
            return self._left.first_in_range(lower_bound, upper_bound, comparator, f)
        elif cr_left is ComparisonResult.AFTER:
            #range fully right of node
            if self._right is None:
                return None
            return self._right.first_in_range(lower_bound, upper_bound, comparator, f)
        else:
            return f(self)

    def _update_after_insert(self, auto_balance : bool):
        self._update_lbs()
        if auto_balance:
            if self._balance > 1:
                self._rotate_right(True)
            elif self._balance < -1:
                self._rotate_left(True)
        if self._parent is not None:
            self._parent._update_after_insert(auto_balance)

    def _update_lbs(self):
        """
        updates level, balance and size of the binary tree
        """
        self._level = max(0 if self._left is None else self._left._level,
                          0 if self._right is None else self._right._level) + 1

        self._balance = (0 if self._left is None else self._left._level + 1) - (
            0 if self._right is None else self._right._level + 1)

        self._size = (0 if self._left is None else self._left._size) + (
            0 if self._right is None else self._right._size) + 1

    def _rotate_right(self, perform_subrotation : bool):
        pivot = self._left
        if pivot._balance < 0 and perform_subrotation:
            pivot._rotate_left(False)
            pivot = self._left #pivot changed
        if self._parent is not None:
            if self._parent._left is self:
                self._parent._update_left(pivot)
            else:
                self._parent._update_right(pivot)
        else:
            pivot._parent = None
        self._update_left(pivot._right)
        pivot._update_right(self)

    def _rotate_left(self, perform_subrotation : bool):
        pivot = self._right
        if pivot._balance > 0 and perform_subrotation:
            pivot._rotate_right(False)
            pivot = self._right #pivot changed
        if self._parent is not None:
            if self._parent._left is self:
                self._parent._update_left(pivot)
            else:
                self._parent._update_right(pivot)
        else:
            pivot._parent = None
        self._update_right(pivot._left)
        pivot._update_left(self)

    def _update_left(self, left : Node[V,K]):
        self._left = left
        if left is not None:
            left._parent = self
        self._update_lbs()

    def _update_right(self, right : Node[V,K]):
        self._right = right
        if right is not None:
            right._parent = self
        self._update_lbs()

    @property
    def key(self) -> K:
        return self._key

    @property
    def value(self) -> V:
        return self._value

    @property
    def left(self) -> Node[K, V]:
        return self._left

    @property
    def right(self) -> Node[K, V]:
        return self._right

    @property
    def parent(self) -> Node[K, V]:
        return self._parent

    @property
    def level(self) -> int:
        return self._level

    @property
    def balance(self) -> int:
        return self._balance

    @property
    def size(self) -> int:
        return self._size

    @property
    def root(self) -> Node[K, V]:
        if self._parent is not None:
            return self._parent.root
        return self

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

    def first_in_range(self, lower_bound : K, upper_bound : K, f: Callable[[Node[K, V]], A] = lambda n: n.key) -> Node[K,V] | None:
        if self._root is None:
            return None
        return self._root.first_in_range(lower_bound, upper_bound, self._comparator, f)

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
        splitting_node = self._root.first_in_range(lower_bound, upper_bound, self._comparator, lambda n: n)
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