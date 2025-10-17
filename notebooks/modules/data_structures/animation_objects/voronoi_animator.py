from ...geometry import AnimationObject, AppendEvent, DeleteAtEvent, MultiEvent, PointPair, Point, PointFloat, PointList
from ..objects import Vertex, Face, HalfEdge
from ..triangle_tree import Triangulation
from .delaunay_animator import IncrementalConstructionAnimator


class VoronoiAnimator(AnimationObject):
    def __init__(self,delaunay_animator : IncrementalConstructionAnimator):
        super().__init__()
        self._vertices : list[Point] = []
        self._delaunay_animator = delaunay_animator

    def add_point(self, point : Point, face : Face):
        point_list = PointList(point.x, point.y, [], 4)
        self._vertices.append(point_list)
        for connected_face in [e.twin.incident_face for e in face.outer_half_edges()]:
            p = Triangulation.center_of_circumcircle(connected_face.outer_points()[0], connected_face.outer_points()[1],
                                                     connected_face.outer_points()[2])
            point_list.data.append(p)


        points = face.outer_points()
        events = [AppendEvent(PointPair(points[0].x, points[0].y, points[1])),
                  AppendEvent(PointPair(points[1].x, points[1].y, points[2])),
                  AppendEvent(PointPair(points[2].x, points[2].y, points[0]))]
        self._animation_events.append(MultiEvent(events))
        self._animation_events.append(AppendEvent(PointFloat(point.x, point.y, point.distance(points[0]))))
        events = [DeleteAtEvent(-2),
                  DeleteAtEvent(-2),
                  DeleteAtEvent(-2),]
        self._animation_events.append(MultiEvent(events))


    def is_inner_face(self, face : Face) -> bool:
        if face.is_outer:
            return False
        for e in face.outer_half_edges():
            if e.twin.incident_face.is_outer:
                return False
        for v in face.outer_vertices():
            for e in v.outgoing_edges():
                if e.incident_face.is_outer:
                    return False
        return True



    def is_inner_vertex(self, v : Vertex):
        if self._delaunay_animator.outer_face.outer_points().__contains__(v):
            return False
        for p in [edge.destination.point for edge in v.outgoing_edges()]:
            if self._delaunay_animator.outer_face.outer_points().__contains__(p):
                return False
        return True

    def points(self) -> list[Point]:
        delaunay_points = self._delaunay_animator.points()
        for point in delaunay_points:
            point.tag = point.tag + 2
            for connected_point in point.data:
                connected_point.tag = connected_point.tag + 2
        return delaunay_points + self._vertices

