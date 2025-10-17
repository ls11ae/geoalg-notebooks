from ...geometry import AnimationObject, AppendEvent, PopEvent, MultiEvent, Point, PointPair
from ..objects import HalfEdge

class EdgeAnimator(AnimationObject):
    def __init__(self):
        super().__init__()
        self._illegal_edges : list[HalfEdge] = []
        self._checked_edges : list[HalfEdge] = []
        self._highlighted_edge : HalfEdge | None = None


    def highlight_triangle(self, e : HalfEdge):
        if self._highlighted_edge is not None:
            return
        self._highlighted_edge = e
        events = []
        origin = e.origin
        destination = e.destination
        opposing_point = e.next.destination
        events.append(AppendEvent(PointPair(origin.point.x, origin.point.y, destination.point, 1)))
        events.append(AppendEvent(PointPair(destination.point.x, destination.point.y, opposing_point.point, 0)))
        events.append(AppendEvent(PointPair(opposing_point.point.x, opposing_point.point.y, origin.point, 0)))
        origin = e.twin.origin
        destination = e.twin.destination
        opposing_point = e.twin.next.destination
        events.append(AppendEvent(PointPair(destination.point.x, destination.point.y, opposing_point.point, 0)))
        events.append(AppendEvent(PointPair(opposing_point.point.x, opposing_point.point.y, origin.point, 0)))
        self._animation_events.append(MultiEvent(events))

    def un_highlight_triangle(self, is_legal: bool):
        if self._highlighted_edge is not None:
            events = [PopEvent(), PopEvent(), PopEvent(), PopEvent()]
            if is_legal:
                events.append(PopEvent())
            self._animation_events.append(MultiEvent(events))
            self._highlighted_edge = None

    def _highlight_edge(self, e : HalfEdge):
        self._animation_events.append(AppendEvent(PointPair(e.origin.point.x, e.origin.point.y, e.destination.point)))

    def _unhighlight_edge(self):
        self._animation_events.append(PopEvent())

    def add_illegal_edge(self, e : HalfEdge):
        self._illegal_edges.append(e)

    def edge_or_twin_checked(self, e : HalfEdge) -> bool:
        return self._checked_edges.__contains__(e) or self._checked_edges.__contains__(e.twin)

    def add_checked_edge(self, e : HalfEdge):
        self._checked_edges.append(e)
        self._checked_edges.append(e.twin)

    def points(self) -> list[Point]:
        points = []
        for e in self._illegal_edges:
            points.append(e.origin.point)
            points.append(e.destination.point)
        return points
