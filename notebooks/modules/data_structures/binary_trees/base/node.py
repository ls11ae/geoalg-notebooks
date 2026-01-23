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
    def leq(self, upper_bound: K, comparator: Comparator[K], t : TreeTracker[V,K], f: Callable[[Node[K, V]], A]) -> list[A]:
        raise NotImplementedError

    @abstractmethod
    def geq(self, lower_bound: K, comparator: Comparator[K], t : TreeTracker[V,K], f: Callable[[Node[K, V]], A]) -> list[A]:
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
        tracker.track_node_visit(self)
        if self.is_leaf():
            result = [f(self)]
            tracker.track_partial_result(result)
            return result
        result_left = [] if self._left is None else self._left.leaves(tracker, f)
        tracker.track_node_visit(self)
        result_right = [] if self._right is None else self._right.leaves(tracker, f)
        tracker.track_node_visit(self)
        return result_left + result_right

    def level_order(self, levels : list[list[A]], f : Callable[[Node[K,V]], A], depth : int,  root_level : int):
        cur_level = root_level - depth #level of the node assuming a full tree
        levels[depth].append(f(self))
        if self._left is not None:
            self._left.level_order(levels, f, depth + 1, root_level)
        else:
            #fill missing left children entries with None
            for i in range(0, cur_level):
                for j in range(0, 2**i):
                    levels[i+depth+1].append(None)
        if self._right is not None:
            self._right.level_order(levels, f, depth + 1, root_level)
        else:
            #fill missing right children entries with None
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
                return None
            result = self._left.first_in_range(lower_bound, upper_bound, comparator, tracker, f)
            tracker.track_node_visit(self)
            return result
        elif cr_left is ComparisonResult.AFTER:
            #range fully right of node
            if self._right is None:
                return None
            result = self._right.first_in_range(lower_bound, upper_bound, comparator, tracker, f)
            tracker.track_node_visit(self)
            return result
        else:
            #node in range
            result = f(self)
            tracker.track_partial_result(result)
            return result

    def _update_after_insert(self, auto_balance : bool):
        """
        tracks a path upwards from the new node, updating the level, balance and size of all nodes.

        Parameters
        ----------
        auto_balance : bool
            If is true, the tree is rotated for nodes with a balance outside [-1,1]. See _rotate_right/_rotate_left
        """
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
        """
        replaces the current node with its left child.
        For a more detailed overview: https://en.wikipedia.org/wiki/Tree_rotation

        Parameters
        ----------
        perform_subrotation : bool
            If True, the tree will check if the pivots balance is -1 and call pivot._rotate_left before rotating
        """
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
        """
        replaces the current node with its right child.
        For a more detailed overview: https://en.wikipedia.org/wiki/Tree_rotation

        Parameters
        ----------
        perform_subrotation : bool
            If True, the tree will check if the pivots balance is -1 and call pivot._rotate_right before rotating
        """
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
    Can be given to certain methods of the different binary tree implementations to track operations within the method.
    """

    def __init__(self):
        self._events : list[TransitionEvent] = []
        self._last_node : Optional[Node[K,V]] = None
        self._call_stack_depth = 0
        self._last_method_called : str = ""

    def track_method_call(self, routine_name : str):
        """
        Called at the start of every method in the binary_tree and its subclasses or when those methods call subroutines
        """
        self._events.append(MethodCalledEvent(routine_name, self._call_stack_depth))
        self._last_method_called = routine_name
        self._call_stack_depth += 1

    def track_method_return(self, result : Any) -> Any:
        """
        Called at the end of every method in the binary_tree and its subclasses or when those methods call subroutines.

        The return value is used to simply write "return tracker.track_method_return(result)" instead of having
        to create a buffer variable
        """
        self._call_stack_depth -= 1
        self._events.append(MethodReturnedEvent(result, self._last_method_called))
        return result

    def track_node_visit(self, node : Node[K,V]):
        """
        Called at the start of each recursive method call to track descent into the tree
        and after each recursive call finishes to track ascent
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

    def track_partial_result(self, result : Any):
        """
        Called whenever a result is added/created/expanded.
        NOT called when a result is simply passed up the tree.
        """
        self._events.append(ResultAddedEvent(result))

    def reset_last_node(self):
        """
        Resets the internal last_node variable to None.
        The last_node variable is used to determine the type of transition between nodes (see TransitionType enum below).
        Complex methods consisting of multiple sub-calls often do not have a clear transition type associated and
        this method can be used to enforce a default to the START transition.
        """
        self._last_node = None

    def get_methods(self) -> list[MethodCalledEvent]:
        return [event for event in self._events if isinstance(event, MethodCalledEvent) and event.call_stack_depth == 1]

    def get_method_events(self) -> list[list[TransitionEvent]]:
        """
        returns a list containing a list for each method that was called
        """
        result : list[list[TransitionEvent]] = []
        current : list[TransitionEvent] = []
        for event in self._events:
            if isinstance(event, MethodCalledEvent) and event.call_stack_depth == 0:
                result.append(current)
                current = []
            current.append(event)
        if current:
            result.append(current)
        return result

    def get_routine_events(self, routine_name : str) -> list[list[TransitionEvent]]:
        """
        returns all events that happened the during calls of the given routine.
        Each list in the returned list corresponds to one call of the subroutine
        """
        routine_active = False
        call_stack_depth = 0
        result: list[list[TransitionEvent]] = []
        current: list[TransitionEvent] = []
        for event in self._events:
            if routine_active:
                if isinstance(event, MethodCalledEvent):
                    call_stack_depth += 1
                if isinstance(event, MethodReturnedEvent):
                    call_stack_depth -=1
                    if call_stack_depth == 0:
                        routine_active = False
                        result.append(current)
                        current = []
                        continue
                current.append(event)
            if isinstance(event, MethodCalledEvent) and event.name is routine_name:
                routine_active = True
                call_stack_depth += 1
        return result

    def get_nodes(self, f: Callable[[Node[K, V]], A] = lambda n : n.key) -> list[A]:
        return [f(event.node) for event in self._events if isinstance(event, NodeVisitedEvent)]

    def get_transition_types(self) -> list[TransitionType]:
        return [event.transition_type for event in self._events if isinstance(event, NodeVisitedEvent)]

    def get_transition_events(self) -> list[NodeVisitedEvent]:
        return [event for event in self._events if isinstance(event, NodeVisitedEvent)]

    def get_results(self) -> Any:
        return [event.result for event in self._events if isinstance(event, ResultAddedEvent)]

    @property
    def events(self) -> list[TransitionEvent]:
        return self._events


class TransitionType(Enum):
    """
    used to track the transition between different nodes
    """
    START = 0 # the last_node is not set, usually at the start of a method or after calling reset_last_node
    LEFT = 1 # new node is a left child of the last one
    RIGHT = 2 # new node is a right child of the last one
    PARENT = 3 # new node is a parent of the last one
    OTHER = 4 # fail-save


class TransitionEvent:
    def __init__(self):
        pass

class MethodCalledEvent(TransitionEvent):
    def __init__(self, name : str, call_stack_depth : int):
        super().__init__()
        self._name = name
        self._call_stack_depth = call_stack_depth

    @property
    def name(self) -> str:
        return self._name

    @property
    def call_stack_depth(self) -> int:
        return self._call_stack_depth

    def __str__(self):
        return ("Method " if self._call_stack_depth == 0 else "Subroutine ") + self._name + " called"

class MethodReturnedEvent(TransitionEvent):
    def __init__(self, result : Any, name : str):
        super().__init__()
        self._result = result
        self._name = name

    @property
    def result(self) -> Any:
        return self._result

    def __str__(self):
        return "Method " + self._name + " finished with result " + str(self._result)

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
