from __future__ import annotations
from ...data_structures import DoublyConnectedEdgeList, Vertex, HalfEdge, Face
from ...geometry import Rectangle, Point, PointList, Line, AnimationObject, AnimationEvent, AppendEvent, PopEvent, DeleteEvent, MultiEvent, PointPair
from typing import Iterator
from itertools import chain

class DCELAnimator(AnimationObject):
    def __init__(self, boundingBox : Rectangle):
        super().__init__()
        self._dcel : DoublyConnectedEdgeList = DoublyConnectedEdgeList([],[])
        self._points : list[Point] = []
        self._animation_events = []
        self._illformed : bool = False
        self._init_bounding_box(boundingBox)
    
    def _init_bounding_box(self, bounding_box: Rectangle):
        #if the bounding box is illformed, all further calculations don't make sense
        if (bounding_box.left == bounding_box.right) or (bounding_box.lower == bounding_box.upper):
            self._illformed = True
            return

        low_left = Point(bounding_box.left, bounding_box.lower)
        up_left = Point(bounding_box.left, bounding_box.upper)
        up_right = Point(bounding_box.right, bounding_box.upper)
        low_right = Point(bounding_box.right, bounding_box.lower)
        #add bottom left first so it can be accessed easily later
        self._dcel.add_vertex(low_left)
        self._dcel.add_vertex(up_left)
        self._dcel.add_vertex(up_right)
        self._dcel.add_vertex(low_right)
        self._dcel.add_edge_by_points(low_left, up_left)
        self._dcel.add_edge_by_points(up_left, up_right)
        self._dcel.add_edge_by_points(up_right, low_right)
        self._dcel.add_edge_by_points(low_right, low_left)
        #animations
        events = []
        events.append(AppendEvent(PointList(low_left.x, low_left.y, [])))
        events.append(AppendEvent(PointList(up_left.x, up_left.y, [])))
        events.append(AppendEvent(PointList(up_right.x, up_right.y, [])))
        events.append(AppendEvent(PointList(low_right.x, low_right.y, [])))
        events.append(EdgeAddedEvent(low_left, up_left))
        events.append(EdgeAddedEvent(up_left, up_right))
        events.append(EdgeAddedEvent(up_right, low_right))
        events.append(EdgeAddedEvent(low_right, low_left))
        self._animation_events.append(MultiEvent(events))

    def add_edge(self, p1 : Point, p2 : Point):
        self._dcel.add_edge_by_points(p1, p2)
        self._animation_events.append(EdgeAddedEvent(p1, p2))

    def add_point(self, point : Point):
        #used by 3 points on a line
        self._animation_events.append(AppendEvent(Point(point.x, point.y, 4)))
        self._points.append(point)

    def add_vertex_on_edge(self, point : Point, edge : HalfEdge) -> Vertex:
        origin = PointList(edge.origin.x, edge.origin.y, [])
        dest = PointList(edge.destination.x, edge.destination.y, [])
        p = PointList(point.x, point.y, [])
        events = [EdgeRemovedEvent(origin, dest), VertexAddedEvent(point), EdgeAddedEvent(origin, point),
                  EdgeAddedEvent(point, dest)]
        self._animation_events.append(MultiEvent(events))
        v = self._dcel.add_vertex_in_edge(edge, point)
        return v

    def highlight_line(self, l : Line):
        self._animation_events.append(AppendEvent(PointPair(l.p1.x, l.p1.y, l.p2)))

    def unhighlight_line(self, l : Line):
        self._animation_events.append(DeleteEvent(PointPair(l.p1.x, l.p1.y, l.p2)))

    def highlight_edge(self, p1 : Point, p2 : Point):
        self._animation_events.append(AppendEvent(PointPair(p1.x, p1.y, p2, 1)))

    def unhighlight_edge(self, p1 : Point, p2 : Point):
        self._animation_events.append(DeleteEvent(PointPair(p1.x, p1.y, p2, 1)))

    def animate_edge(self, p1 : Point, p2 : Point):
        self._animation_events.append(MultiEvent([AppendEvent(Point(p1.x, p1.y, 2)), AppendEvent(Point(p2.x, p2.y, 2))]))
        self._animation_events.append(MultiEvent([PopEvent(),PopEvent()]))

    def points(self) -> Iterator[Point]:
        points : list[Point] = []
        for v in self._dcel.vertices:
            p = PointList(v.point.x, v.point.y, [])
            points.append(p)
            if v.edge.destination is not v:
                e = v.edge
                p.data.append(Point(e.destination.point.x, e.destination.point.y))
                e = e.twin.next
                while e != v.edge:
                    p.data.append(Point(e.destination.point.x, e.destination.point.y))
                    e = e.twin.next
        points = points + self._points
        return iter(points)
    
    def get_next_face(self, v : Vertex, p : Point) -> Face:
        return self._dcel.find_splitting_face(v,p)
    
    def get_bounding_box(self) -> list[HalfEdge]:
        return self._dcel.outer_face.inner_half_edges()
    
    def get_outer_face(self) -> Face:
        return self._dcel.outer_face
    
    def get_bottom_left(self) -> Vertex:
        return self._dcel.start_vertex
    
    def get_splitting_face(self, v : Vertex, p : Point) -> Face:
        return self._dcel.find_splitting_face(v,p)

    def vertices(self) -> list[Vertex]:
        return self._dcel.vertices

    def faces(self) -> list[Face]:
        return self._dcel.faces

    @property
    def illformed(self):
        return self._illformed



class VertexAddedEvent(AnimationEvent):
    def __init__(self, p: Point):
        super().__init__()
        self._p = PointList(p.x,p.y, [])

    def execute_on(self, points: list[Point]):
        points.append(self._p)

class EdgeAddedEvent(AnimationEvent):
    def __init__(self, p1: Point, p2: Point):
        super().__init__()
        self._p1 = p1
        self._p2 = p2

    def execute_on(self, points : list[Point]):
        for p in points:
            if isinstance(p, PointList):
                if p.x == self._p1.x and p.y == self._p1.y:
                    p.data.append(self._p2)
                if p.x == self._p2.x and p.y == self._p2.y:
                    p.data.append(self._p1)

class EdgeRemovedEvent(AnimationEvent):
    def __init__(self, p1: PointList, p2: PointList):
        super().__init__()
        self._p1 = p1
        self._p2 = p2

    def execute_on(self, points : list[Point]):
        for p in points:
            if isinstance(p, PointList):
                if p.x == self._p1.x and p.y == self._p1.y and p.data.__contains__(self._p2):
                    p.data.remove(self._p2)
                if p.x == self._p2.x and p.y == self._p2.y and p.data.__contains__(self._p1):
                    p.data.append(self._p1)

class StateChangedEvent(AnimationEvent):
    def execute_on(self, data):
        pass

class MinAreaTriangleAnimator(AnimationObject):
    def __init__(self, dcel: DCELAnimator):
        super().__init__()
        self._dcel = dcel
        self._smallest_triangle : list[Point] = []
        self._animation_events = list(dcel.animation_events())
        self._animation_events.append(StateChangedEvent())


    def points(self) -> Iterator[Point]:
        dcel_iter = self._dcel.points()
        points_iter = iter(self._smallest_triangle)
        return chain(dcel_iter, points_iter)

    def add_edge(self, p1 : Point, p2 : Point):
        self._animation_events.append(AppendEvent(PointList(p1.x, p1.y, [p2])))
        self._animation_events.append(AppendEvent(PointList(p2.x, p2.y, [p1])))

    def remove_edge(self):
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())

    def animate_point(self, p1 : Point):
        self._animation_events.append(AppendEvent(p1))
        self._animation_events.append(PopEvent())

    def animate_triangle(self, p1 : Point, p2 : Point, p3 : Point):
        self._animation_events.append(AppendEvent(p1))
        self._animation_events.append(AppendEvent(p1))
        self._animation_events.append(AppendEvent(p1))
        self.add_edge(p1,p2)
        self.add_edge(p2,p3)
        self.add_edge(p3,p1)
        
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())

        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())
        self._animation_events.append(PopEvent())

    def add_point(self, p : Point):
        self._animation_events.append(AppendEvent(p))

    def remove_point(self):
        self._animation_events.append(PopEvent())

    @property
    def smallest_triangle(self) -> list[Point]:
        return self._smallest_triangle
    
    @smallest_triangle.setter
    def smallest_triangle(self, value):
        self._smallest_triangle = value

    @property
    def dcel(self) -> DCELAnimator:
        return self._dcel