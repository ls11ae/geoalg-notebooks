from abc import ABC, abstractmethod
import time
from typing import Callable, Generic, TypeVar, Union
import numpy as np

from .drawing import DrawingMode
from ..geometry import AnimationObject,  Point, PointReference


I = TypeVar("I") #generic type for the input of an algorithm

Algorithm = Callable[[I], AnimationObject] #type of the algorithm itself, input of type I, output of type Animation Object
"""
General class to handle all instances of visualisation.

Holds an instance of type I (for example a set of points) that gets used as an input to whatever algorithm is called

"""
class InstanceHandle(ABC, Generic[I]):
    """
    This class is used to run an algorithm on an input.
    The Input has type I, the algorithm must take a single parameter of that type and return an AnimationObject

    Attributes
    ----------
    _instance : I
        the input to the algorithm
    _drawing_mode : DrawingMode
        defines how the instance is drawn/animated
    _default_number_of_random_points : int
        the default number of randomly generated points when the random button is pressed

    Methods
    ----------
    """
    
    def __init__(self, instance: I, drawing_mode: DrawingMode, default_number_of_random_points : int):
        self._instance = instance
        self._drawing_mode = drawing_mode
        self._default_number_of_random_points = default_number_of_random_points

    # -------- methods --------

    def run_algorithm(self, algorithm: Algorithm[I]) -> tuple[AnimationObject, float]:
        """
        Runs the algorithm with this instance as input. Returns the algoriths output and the time taken.
        """
        instance_points = self.extract_points_from_raw_instance(self._instance)

        start_time = time.perf_counter()
        algorithm_output = algorithm(self._instance)
        end_time = time.perf_counter()

        self.clear()
        for point in instance_points:
            self.add_point(point)

        return algorithm_output, 1000 * (end_time - start_time)
    
    def run_algorithm_with_preprocessing(self, preprocessing: Algorithm[I], algorithm: Algorithm[I]) -> tuple[AnimationObject, float]:
        """
        Runs a preprocessing algorithm and then the algorithm with this instance as input.
        Returns the algoriths output and the time taken.
        Time taken does not take preprocessing into account.
        """
        instance_points = self.extract_points_from_raw_instance(self._instance)

        preprocessing(self._instance)

        start_time = time.perf_counter()
        algorithm_output = algorithm(self._instance)
        end_time = time.perf_counter()

        self.clear()
        for point in instance_points:
            self.add_point(point)

        return algorithm_output, 1000 * (end_time - start_time)

    # -------- abstact methods --------

    @abstractmethod
    def add_point(self, point: Point) -> Union[bool, tuple[bool, Point]]:
        """
        Adds a point to the instance.
        The bool return is true if the point was sucessfully added and false otherwise.
        The tuple return is used to also return the point in case the point was changed in some way.
        
        Note: This return value is used for the dcel_instance since the connecting edges are also need during drawing.
        Since this is not very clean, it should be replaced
        1. replace by Point | None and check ret == None, this simplifies return type and reduces code in tool
        2. replace by list[Point] (empty list equals false), this is similar to 1. but allows for more generalization
        if future instances require multiple points to be added per click
        """
        pass

    @abstractmethod
    def clear(self):
        """
        Removes all points from the instance
        """
        pass

    @abstractmethod
    def size(self) -> int:
        """
        Returns the number of points or some equivalent size measurement.
        """
        pass

    @abstractmethod
    def generate_random_points(self, max_x : float, max_y : float, number : int):
        """
        Used by the tool to generate random points for the instance when the random button is pressed.
        Use the generate_random_points_uniform and generate_random_points_gaussian methods to avoid
        duplicate code.
        """
        pass

    # -------- static --------

    @staticmethod
    def generate_random_points_uniform(max_x: float, max_y: float, number: int) -> list[Point]:
        """
        Generates a list of random points with coordinates sampled from a uniform distribution 
        over the interval [0, max_x) and [0, max_y)
        """
        x_values = np.random.uniform(0.05 * max_x, 0.95 * max_x, number)
        y_values = np.random.uniform(0.05 * max_y, 0.95 * max_y, number)
        return [Point(x, y) for x, y  in zip(x_values, y_values)]
    
    @staticmethod
    def generate_random_points_gaussian(max_x: float, max_y: float, number: int) -> list[Point]:
        """
        Generates a list of random points with coordinates sampled from a guassian distribution 
        over the interval [0, max_x) and [0, max_y)
        """
        x_values = np.clip(np.random.normal(0.5 * max_x, 0.15 * max_x, number), 0.05 * max_x, 0.95 * max_x)
        y_values = np.clip(np.random.normal(0.5 * max_y, 0.15 * max_y, number), 0.05 * max_y, 0.95 * max_y)
        return [Point(x, y) for x, y in zip(x_values, y_values)]
    
    @staticmethod
    @abstractmethod
    def extract_points_from_raw_instance(instance: I) -> list[Point] | list[PointReference]:
        """
        Returns a list of Points based on the given instance.

        TODO: find out why this is static instead of having a self.points method
        """
        pass
    
    # -------- properties --------

    @property
    def drawing_mode(self) -> DrawingMode:
        return self._drawing_mode

    @property
    def default_number_of_random_points(self) -> int:
        return self._default_number_of_random_points
    
    @default_number_of_random_points.setter
    def number_of_points(self, value):
        self._default_number_of_random_points = value