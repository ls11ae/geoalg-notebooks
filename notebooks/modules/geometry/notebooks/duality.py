from ..core import Point, Line, LineSegment

def dual_point(p : Point) -> Line:
    return Line.line_from_m_b(p.x, -p.y)

def dual_line(l : Line) -> Point:
    return Point(l.slope(), -l.y_from_x(0))

def dual_lineSegment(ls : LineSegment) -> tuple[Line,Line]:
    return [dual_point(ls.upper), dual_point(ls.lower)]

def dual_points(points : list[Point]) -> list[Line]:
    return [dual_point(p) for p in points]

def dual_lines(lines : list[Line]) -> list[Point]:
    return [dual_line(l) for l in lines]

def dual_lineSegments(line_segements : list[LineSegment]) -> list[tuple[Line,Line]]:
    return [dual_lineSegment(lS) for lS in line_segements]