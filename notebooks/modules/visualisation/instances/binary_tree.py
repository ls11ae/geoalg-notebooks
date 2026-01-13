from typing import override

from ...data_structures.binary_trees import EST
from ...geometry import Point, PointXComparator
from ..drawing_modes import BinaryTreeMode
from ..instance_handle import InstanceHandle

class BinaryTreeInstance(InstanceHandle[EST[Point]]):
    def __init__(self):
        self._instance = EST[Point](PointXComparator(), True)
        drawing_mode = BinaryTreeMode()
        drawing_mode.binary_tree = self._instance
        super().__init__(set(), drawing_mode, 10)

    @override
    def add_point(self, point: Point) -> Point | None:
        point.__round__()
        if self._instance.insert(point):
            return point
        return None

    @override
    def clear(self):
        self._instance = EST[Point](PointXComparator(), True)
        self._drawing_mode.binary_tree = self._instance

    @override
    def size(self) -> int:
        return 0

    @staticmethod
    @override
    def extract_points_from_raw_instance(instance: set[Point]) -> list[Point]:
        return []

    @override
    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        return BinaryTreeInstance.generate_random_points_uniform(max_x, max_y, number)