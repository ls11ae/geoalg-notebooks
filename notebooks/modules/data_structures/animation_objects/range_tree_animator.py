from __future__ import annotations
from ...geometry.animation_base import AnimationObject, AppendEvent, SetEvent, MultiEvent
from ...geometry.core import Rectangle, Point
from typing import Iterator

class RangeTreeAnimator(AnimationObject):

    def __init__(self):
        super().__init__()

    def points(self) -> Iterator[Point]:
        pass