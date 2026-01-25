from typing import override
import time
from ...data_structures.binary_trees import EST
from ...geometry import Point, IntComparator, AnimationObject
from ..drawing_modes import BinaryTreeMode
from ..instance_handle import InstanceHandle, I, Algorithm

class BinaryTreeInstance(InstanceHandle[EST[int]]):
    def __init__(self):
        super().__init__(EST[int](IntComparator(), True),  BinaryTreeMode(), 10)
        self._drawing_mode.binary_tree = self._instance


    @override
    def add_point(self, point: Point) -> Point | None:
        point.__round__()
        if self._instance.insert(int(point.x)):
            return point
        return None

    @override
    def clear(self):
        self._instance = EST[int](IntComparator(), True)
        self._drawing_mode.binary_tree = self._instance

    @override
    def size(self) -> int:
        return 0

    @staticmethod
    @override
    def extract_points_from_raw_instance(instance: EST[Point]) -> list[Point]:
        return []

    @override
    def generate_random_points(self, max_x: float, max_y: float, number: int) -> list[Point]:
        return BinaryTreeInstance.generate_random_points_uniform(max_x, max_y, number)

    @override
    def run_algorithm(self, algorithm: Algorithm[I]) -> tuple[AnimationObject, float]:
        """
        Runs the algorithm with refilling the tree
        """

        start_time = time.perf_counter()
        algorithm_output = algorithm(self._instance)
        end_time = time.perf_counter()

        return algorithm_output, 1000 * (end_time - start_time)