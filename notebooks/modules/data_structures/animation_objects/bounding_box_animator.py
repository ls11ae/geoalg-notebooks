from __future__ import annotations
from ...geometry.animation_base import AnimationObject, AppendEvent, SetEvent, PopEvent
from ...geometry.core import Rectangle, Point
from typing import Iterator

class BoundingBoxAnimator(AnimationObject):    
    '''An axis aligned bounding box that expands based on new points added via the update method

    Attributes
    ----------
    _bounding_box : Rectangle
        the current limits of the bounding box
    _initialized : bool
        false when no points have yet been added and the boundaries are still undefined

    Methods
    -------
    isInside(point)
        returns wether the given point is inside the rectangle or not
    isOnBoundary(point)
        returns wether the given point is on the boundary or not
    isOutside(point)
        returns wether the given point is outside the rectangle or not 
        (equal to !isInside and !isOnBoundary)
    expand(point)
        increases the rectangles boundary to contain the given point
        does nothing if the point is already within the boundary
    '''

    def __init__(self):
        super().__init__()
        self._bounding_box : Rectangle = None

    def update(self, point : Point):
        'Updates the boundary of the bounding box to contain the given point.'
        if (self._bounding_box is None):
            #append 4 points to have 4 initial cornerpoints
            self._bounding_box = Rectangle(point, point)
            self._animation_events.append(AppendEvent(point))
            self._animation_events.append(AppendEvent(point))
            self._animation_events.append(AppendEvent(point))
            self._animation_events.append(AppendEvent(point))
            return
        #update bounding box and animation
        self._animation_events.append(AppendEvent(point))
        self._animation_events.append(PopEvent())
        self._bounding_box.expand(point)
        for i, p in enumerate(self.points()):
            self._animation_events.append(SetEvent(i, p))

    def points(self) -> Iterator[Point]:
        '''Returns the four corner of the bounding box in clockwise order, starting at the bottom left.
        If the bounding box was not initialized by adding a point via update, returns an empty list instead.
        '''
        if self._bounding_box is None:
             return iter([])
        return iter([Point(self._bounding_box.left, self._bounding_box.lower), 
                     Point(self._bounding_box.left, self._bounding_box.upper), 
                     Point(self._bounding_box.right, self._bounding_box.upper), 
                     Point(self._bounding_box.right, self._bounding_box.lower)])

    @property
    def boundingBox(self) -> Rectangle | None:
        '''Returns the current bounding box as a rectangle. 
        If the bounding box was not initialized by adding a point via update, returns None instead.
        '''
        return self._bounding_box