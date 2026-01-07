from __future__ import annotations
from typing import TypeVar, Generic, Optional, List, Callable
from abc import ABC, abstractmethod
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
        pass

    @abstractmethod
    def delete(self, key : K , comparator : Comparator[K]) -> bool:
        pass

    def path(self, key : K, comparator : Comparator[K]) -> list[Node[K, V]]:
        """
        returns the full path to the first node containing the given key. If the key is not found, an empty list is returned.
        """
        cr = comparator.compare(key, self._key)
        if cr is ComparisonResult.BEFORE or cr is ComparisonResult.MATCH:
            if self._left is None:
                return [self]
            else:
                path = self._left.path(key, comparator)
                return [] if path is [] else [self] + path
        else:
            if self._right is None:
                return [self]
            else:
                path = self._right.path(key, comparator)
                return [] if path is [] else [self] + path

    def path_to_leaf(self, key : K, comparator : Comparator[K]) -> List[Node[K, V]]:
        """
        returns the full path to the leaf containing the given key. Ignores all earlier findings of the key.
        If the key is not found, an empty list is returned.
        """
        if self.is_leaf():
            return [self]
        cr = comparator.compare(key, self._key)
        path = None
        if cr is ComparisonResult.BEFORE or cr is ComparisonResult.MATCH:
            if self._left is None:
                path = self._right.path_to_leaf(key, comparator)
            else:
                path = self._left.path_to_leaf(key, comparator)
        else:
            if self._right is None:
                path = self._left.path_to_leaf(key, comparator)
            else:
                path = self._right.path_to_leaf(key, comparator)
        return [] if path is [] else [self] + path

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

    def _update_after_insert(self, auto_balance : bool):
        self._update_level()
        self._update_balance()
        self._update_size()
        if auto_balance:
            if self._balance > 1:
                 self._rotate_right()
            elif self._balance < -1:
                self._rotate_left()
        if self._parent is not None:
            self._parent._update_after_insert(auto_balance)

    def _update_level(self):
        self._level = max(0 if self._left is None else self._left._level, 0 if self._right is None else self._right._level) + 1

    def _update_balance(self):
        self._balance = (0 if self._left is None else self._left._level) - (0 if self._right is None else self._right._level)

    def _update_size(self):
        self._size = (0 if self._left is None else self._left._size) + (0 if self._right is None else self._right._size) + 1

    def _rotate_right(self):
        pivot = self._left
        if pivot._balance < 0:
            pivot._rotate_left()
            pivot = self._left #pivot changed
        if self._parent is not None:
            if self._parent._left is self:
                self._parent.left = pivot
            else:
                self._parent.right = pivot
        else:
            pivot._parent = None
        self.left = pivot._right
        pivot.right = self
        self._update_level()
        self._update_balance()
        self._update_size()

    def _rotate_left(self):
        pivot = self._right
        if pivot._balance > 0:
            pivot._rotate_right()
            pivot = self._right #pivot changed
        if self._parent is not None:
            if self._parent._left is self:
                self._parent.left = pivot
            else:
                self._parent.right = pivot
        else:
            pivot._parent = None
        self.right = pivot._left
        pivot.left = self
        self._update_level()
        self._update_balance()
        self._update_size()

    @property
    def key(self) -> K:
        return self._key

    @property
    def value(self) -> V:
        return self._value

    @property
    def left(self) -> Node[K, V]:
        return self._left

    @left.setter
    def left(self, left: Node[K, V]):
        self._left = left
        if left is not None:
            left._parent = self
        self._update_level()
        self._update_balance()

    @property
    def right(self) -> Node[K, V]:
        return self._right

    @right.setter
    def right(self, right: Node[K, V]):
        self._right = right
        if right is not None:
            right._parent = self
        self._update_level()
        self._update_balance()

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

    def path(self, key : K) -> list[Node[K, None]]:
        if self._root is not None:
            return self._root.path(key, self._comparator)
        return []

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

    def level_order(self) -> list[list[K]]:
        if self._root is None:
            return []
        queue = [self._root]
        nodes = []
        while queue:
            layer = []
            layer_size = len(queue)
            for n in range(0, layer_size):
                node = queue.pop(0)
                if node is not None:
                    layer.append(node.key)
                    queue.append(node.left)
                    queue.append(node.right)
                else:
                    layer.append(None)
            nodes.append(layer)
        return nodes

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