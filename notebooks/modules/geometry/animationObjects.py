'''
This file contains classes that are used as output by algorithms that need to be drawn (and animated).
The type variable 'O' is the output of an algorithm, eg.: an algorithm that returns a list of edges can return
an AnimationObject[list[edges]]
'''
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Iterator
from core import Point

OUT = TypeVar['OUT']

class AnimationObject(ABC, Generic[OUT]):     # TODO: Rename, move and export this.
    @abstractmethod
    def points(self) -> Iterator[Point]:
        pass

    
class AnimationEvent(ABC, Generic[OUT]):
    
    @abstractmethod
    def execute_event(self, data : OUT):
        pass