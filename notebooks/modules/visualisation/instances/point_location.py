from typing import Optional, Union, override

from ...data_structures import DoublyConnectedEdgeList, PointLocation
from ...geometry import PointReference
from ..drawing import DrawingMode
from ..drawing_modes import DCELMode
from ..instance_handle import InstanceHandle
from .dcel import DCELInstance

class PointLocationInstance(DCELInstance, InstanceHandle[PointLocation]):
    def __init__(self, drawing_mode: Optional[DrawingMode] = None, drawing_epsilon: float = 5, random_seed: Optional[int] = None):
        if drawing_mode is None:
            drawing_mode = DCELMode(point_radius = 3)
        self._drawing_mode = drawing_mode
        self._drawing_epsilon = drawing_epsilon
        self._last_added_point = None
        self._instance = PointLocation(random_seed=random_seed)
        self._dcel = self._instance._dcel
        self._default_number_of_random_points = 20

    @staticmethod
    @override
    def extract_points_from_raw_instance(instance: Union[DoublyConnectedEdgeList, PointLocation]) -> list[PointReference]:
        if isinstance(instance, DoublyConnectedEdgeList):
            return DCELInstance.extract_points_from_raw_instance(instance)
        else:
            return DCELInstance.extract_points_from_raw_instance(instance._dcel)
        