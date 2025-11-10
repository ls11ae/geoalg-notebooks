from __future__ import annotations
from typing import TypeVar, Generic, Optional, Any, override, List, Tuple
from enum import Enum
from abc import ABC, abstractmethod

K = TypeVar("K")
V = TypeVar("V")

class ComparisonResult(Enum):
    BEFORE = -1
    MATCH = 0
    AFTER = 1

class Comparator(ABC, Generic[K]):
    @abstractmethod
    def compare(self, key: K, other: K) -> ComparisonResult:
        pass

class Node(Generic[K, V], ABC):
    """Abstract node that implements a tree structure.

    Attributes
    ----------
    _key : Optional[K]
        key used for comparisons when searching in the tree
    _value : Optional[V]
        value of the node
    _left : Optional[Node[K, V]]
        left child
    _right : Optional[Node[K, V]]
        right child
    _parent : Optional[Node[K, V]]
        parent node
    _level : int
        level of the Node in a tree, 1 = leaf, 2+ = inner node

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
        self._level : int = 1

    def is_leaf(self) -> bool:
        return self._left is None and self._right is None

    def is_root(self) -> bool:
        return self._parent is None

    @abstractmethod
    def insert(self, key: K, value: V, comparator : Comparator[K]):
        pass

    @abstractmethod
    def delete(self, key : K , comparator : Comparator[K]):
        pass

    @staticmethod
    def keys(nodes: List[Optional[Node[K, V]]]) -> List[Optional[K]]:
        return [None if node is None else node.key for node in nodes]

    @staticmethod
    def values(nodes : List[Optional[Node[K, V]]]) -> List[Optional[V]]:
        return [None if node is None else node.value for node in nodes]

    @staticmethod
    def keys_and_values(nodes: List[Optional[Node[K, V]]]) -> List[Optional[Tuple[K, V]]]:
        return [None if node is None else (node.key, node.value) for node in nodes]

    def pre_order(self) -> List[Optional[Node[K, V]]]:
        return ([self] +
                ([None] if self._left is None else self._left.pre_order())+
                ([None] if self._right is None else self._right.pre_order()))

    def post_order(self) -> List[Node[K, V]]:
        return (([None] if self._left is None else self._left.post_order()) +
                ([None] if self._right is None else self._right.post_order()) +
                [self])

    def in_order(self) -> List[Node[K, V]]:
        return (([None] if self._left is None else self._left.in_order()) +
                [self] +
                ([None] if self._right is None else self._right.in_order()))

    def reverse_pre_order(self) -> List[Node[K, V]]:
        return ([self] +
                ([None] if self._right is None else self._right.reverse_pre_order()) +
                ([None] if self._left is None else self._left.reverse_pre_order()))

    def reverse_post_order(self) -> List[Node[K, V]]:
        return (([None] if self._right is None else self._right.reverse_post_order()) +
                ([None] if self._left is None else self._left.reverse_post_order()) +
                [self])

    def reverse_in_order(self) -> List[Node[K, V]]:
        return (([None] if self._right is None else self._right.reverse_in_order()) +
                [self] +
                ([None] if self._left is None else self._left.reverse_in_order()))

    def leaves(self) -> List[Node[K, V]]:
        if self.is_leaf():
            return [self]
        return (([] if self._left is None else self._left.leaves()) +
                ([] if self._right is None else self._right.leaves()))

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
        left._parent = self

    @property
    def right(self) -> Node[K, V]:
        return self._right

    @right.setter
    def right(self, right: Node[K, V]):
        self._right = right
        right._parent = self

    @property
    def parent(self) -> Node[K, V]:
        return self._parent

    @property
    def level(self) -> int:
        return self._level

    @level.setter
    def level(self, level: int):
        self._level = level
        self._parent.level = max(self._parent._left._level, self._parent._right._level)