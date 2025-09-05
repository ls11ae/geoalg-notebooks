from .fixed_vertex_number_paths import FixedVertexNumberPathsMode

from ..drawing import (
    DEFAULT_POINT_RADIUS, DEFAULT_HIGHLIGHT_RADIUS, DEFAULT_LINE_WIDTH
)

class LineSegmentsMode(FixedVertexNumberPathsMode):
    def __init__(self, vertex_radius: int = DEFAULT_POINT_RADIUS,
    highlight_radius: int = DEFAULT_HIGHLIGHT_RADIUS, line_width: int = DEFAULT_LINE_WIDTH):
        super().__init__(2, vertex_radius, highlight_radius, line_width)