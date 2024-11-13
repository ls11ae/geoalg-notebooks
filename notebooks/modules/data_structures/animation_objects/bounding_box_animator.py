from __future__ import annotations
from ...geometry.animation_base import AnimationObject, AppendEvent, DeleteAtEvent, MultiSetEvent, SetEvent
from ...geometry.core import Rectangle, Point
from typing import Iterator

LEFT_LOWER_INDEX = 0
LEFT_UPPER_INDEX = 1
RIGHT_UPPER_INDEX = 2
RIGHT_LOWER_INDEX = 3

class BoundingBoxAnimator(AnimationObject):    

    def __init__(self):
        self._boundingBox : Rectangle = Rectangle(Point(0,0), Point(0,0))
        self._initialized = False
        self._animation_events = []

    def _update_Left(self, left : float):
        self._boundingBox.left = left
        self._update_left_lower()
        self._update_left_upper()

    def _update_Right(self, right : float):
        self._boundingBox.right = right
        self._update_right_lower()
        self._update_right_upper()

    def _update_Lower(self, lower : float):
        self._boundingBox.lower = lower
        self._update_left_lower()
        self._update_right_lower()

    def _update_Upper(self, upper : float):
        self._boundingBox.upper = upper
        self._update_left_upper()
        self._update_right_upper()


    def _update_left_lower(self):
        new_left_lower = Point(self._boundingBox.left, self._boundingBox.lower)
        self._animation_events.append(SetEvent(LEFT_LOWER_INDEX, new_left_lower))

    def _update_right_lower(self):
        new_right_lower = Point(self._boundingBox.right, self._boundingBox.lower)
        self._animation_events.append(SetEvent(RIGHT_LOWER_INDEX, new_right_lower))

    def _update_right_upper(self):
        new_right_upper = Point(self._boundingBox.right, self._boundingBox.upper)
        self._animation_events.append(SetEvent(RIGHT_UPPER_INDEX, new_right_upper))

    def _update_left_upper(self):
        new_left_upper = Point(self._boundingBox.left, self._boundingBox.upper)
        self._animation_events.append(SetEvent(LEFT_UPPER_INDEX, new_left_upper))

    
    def check_candidate(self, candidate : Point):
        if (not self._initialized):
            self._initialized = True
            #append 4 points to have 4 initial cornerpoints
            self._boundingBox = Rectangle(candidate, candidate)
            self._animation_events.append(AppendEvent(candidate))
            self._animation_events.append(AppendEvent(candidate))
            self._animation_events.append(AppendEvent(candidate))
            self._animation_events.append(AppendEvent(candidate))
            return
        
        self._animation_events.append(AppendEvent(candidate))
        if(candidate.x < self._boundingBox.left):
            self._update_Left(candidate.x)
        if(candidate.x > self._boundingBox.right):
            self._update_Right(candidate.x)
        if(candidate.y < self._boundingBox.lower):
            self._update_Lower(candidate.y)
        if(candidate.y > self._boundingBox.upper):
            self._update_Upper(candidate.y)
        self._animation_events.append(DeleteAtEvent(4))

    def points(self) -> Iterator[Point]:
        if not self._initialized:
             return iter([])
        return iter([Point(self._boundingBox.left, self._boundingBox.lower), 
                     Point(self._boundingBox.left, self._boundingBox.upper), 
                     Point(self._boundingBox.right, self._boundingBox.upper), 
                     Point(self._boundingBox.right, self._boundingBox.lower)])

    @property
    def boundingBox(self):
        return self._boundingBox