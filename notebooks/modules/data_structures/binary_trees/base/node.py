from __future__ import annotations
from enum import Enum
from typing import TypeVar, Generic, Optional, Callable, Any
from abc import ABC, abstractmethod

from ....geometry import Comparator, ComparisonResult

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
    def report_leq(self, upper_bound: K, comparator: Comparator[K], t : TreeTracker[V,K],f: Callable[[Node[K, V]], A]) -> list[A]:
        raise NotImplementedError

    @abstractmethod
    def report_geq(self, lower_bound: K, comparator: Comparator[K], t : TreeTracker[V,K],f: Callable[[Node[K, V]], A]) -> list[A]:
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

    def leaves(self,tracker : TreeTracker[K,V], f : Callable[[Node[K,V]], A]) -> list[A]:
        if tracker:
            tracker.track_node_visit(self)
        if self.is_leaf():
            result = [f(self)]
            if tracker:
                tracker.track_result(result)
            return result
        result_left = [] if self._left is None else self._left.leaves(tracker, f)
        tracker.track_node_visit(self)
        result_right = [] if self._right is None else self._right.leaves(tracker, f)
        tracker.track_node_visit(self)
        return result_left + result_right

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

    def first_in_range(self, lower_bound: K, upper_bound: K, comparator : Comparator[K], tracker : TreeTracker[K,V], f : Callable[[Node[K,V]], A]) -> A | None:
        tracker.track_node_visit(self)
        cr_left = comparator.compare(lower_bound, self._key)
        cr_right = comparator.compare(upper_bound, self._key)
        if cr_right is ComparisonResult.BEFORE:
            #range fully left of node
            if self._left is None:
                tracker.track_result(None)
                return None
            result = self._left.first_in_range(lower_bound, upper_bound, comparator, tracker, f)
            tracker.track_node_visit(self)
            return result
        elif cr_left is ComparisonResult.AFTER:
            #range fully right of node
            if self._right is None:
                #tracker.result_added(None)
                return None
            result = self._right.first_in_range(lower_bound, upper_bound, comparator, tracker, f)
            tracker.track_node_visit(self)
            return result
        else:
            #node in range
            result = f(self)
            tracker.track_result(result)
            return result

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


class TreeTracker(Generic[K,V]):
    """
    can be given to certain methods of the binary tree implementations to track actions happening in those methods.
    """

    def __init__(self):
        self._events : list[TransitionEvent] = []
        self._last_node : Optional[Node[K,V]] = None

    def track_node_visit(self, node : Node[K,V]):
        """
        called at the start of each recursive function to track descent into tree
        called after each recursive call to track ascend to top
        """
        transition_type = TransitionType.START
        if self._last_node is not None:
            if self._last_node.parent is node:
                transition_type = TransitionType.PARENT
            elif self._last_node.left is node:
                transition_type = TransitionType.LEFT
            elif self._last_node.right is node:
                transition_type = TransitionType.RIGHT
            else:
                transition_type = TransitionType.OTHER
        self._events.append(NodeVisitedEvent(node, transition_type))
        self._last_node = node

    def track_result(self, result : Any):
        """
        called when the return value of a method is changed, either storing the new value
        or the changed value
        """
        self._events.append(ResultAddedEvent(result))

    def track_subroutine_call(self, routine_name : str):
        self._events.append(SubroutineCalledEvent(routine_name))

    def reset_last_node(self):
        self._last_node = None

    @property
    def events(self) -> list[TransitionEvent]:
        return self._events

    @property
    def visited_nodes(self, f: Callable[[Node[K, V]], A] = lambda n : n.key) -> list[A]:
        return [f(event.node) for event in self._events if isinstance(event, NodeVisitedEvent)]

    @property
    def transition_types(self) -> list[TransitionType]:
        return [event.transition_type for event in self._events if isinstance(event, NodeVisitedEvent)]

    @property
    def transition_events(self) -> list[NodeVisitedEvent]:
        return [event for event in self._events if isinstance(event, NodeVisitedEvent)]

    @property
    def results(self) -> Any:
        return [event.result for event in self._events if isinstance(event, ResultAddedEvent)]


class TransitionType(Enum):
    START = 0
    LEFT = 1
    RIGHT = 2
    PARENT = 3
    OTHER = 4


class TransitionEvent:
    def __init__(self):
        pass


class NodeVisitedEvent(Generic[K,V], TransitionEvent):
    def __init__(self, node : Node[K,V], transition_type : TransitionType):
        super().__init__()
        self._node : Node[V,K] = node
        self._transition_type : TransitionType = transition_type

    @property
    def node(self) -> Node[K,V]:
        return self._node

    @property
    def transition_type(self) -> TransitionType:
        return self._transition_type

    def __str__(self):
        return "Node " + str(self._node.key) + " visited via " + str(self._transition_type)


class ResultAddedEvent(TransitionEvent):
    def __init__(self, result : Any):
        super().__init__()
        self._result : Any = result

    @property
    def result(self):
        return self._result

    def __str__(self):
        return "Result " + str(self._result) + " added"

class SubroutineCalledEvent(TransitionEvent):
    def __init__(self, name : str):
        super().__init__()
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __str__(self):
        return "Subroutine " + self._name + " called"