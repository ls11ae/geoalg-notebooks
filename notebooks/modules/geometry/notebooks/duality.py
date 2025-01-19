from ..core import Point, Line, LineSegment

def dual_point(p : Point) -> Line:
    return Line.line_from_m_b(p.x, -p.y)

def dual_line(l : Line) -> Point | None:
    m_b = l.get_m_b()
    if type(m_b) is None:
        return None
    return Point(m_b[0], -m_b[1])

def dual_lineSegment(ls : LineSegment) -> tuple[Line,Line]:
    return [dual_point(ls.upper), dual_point(ls.lower)]
