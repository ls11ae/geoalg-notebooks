from notebooks.modules.data_structures import DoublyConnectedEdgeList, DoublyConnectedSimplePolygon
from notebooks.modules.geometry import Point, PointReference, LineSegment
from notebooks.modules.data_structures import monotone_triangulation, recursive_triangulation
from notebooks.modules.data_structures.vertical_decomposition import PointLocation, VDLineSegment
from notebooks.modules.geometry import Rectangle

def main():
    """ Testing """

    s = 50
    t = 350
    u = (t - s) / 30

    points = [Point(s + 20*u, t),        Point(s + 26*u, t -  6*u), Point(s + 30*u, t -  8*u), Point(s + 28*u, t - 10*u),
            Point(s + 18*u, t - 12*u), Point(s + 29*u, s + 14*u), Point(s + 27*u, s +  6*u), Point(s + 22*u, s +  1*u),
            Point(s + 14*u, s +  4*u), Point(s + 10*u, s),        Point(s +  2*u, s +  5*u), Point(s + 12*u, s + 12*u),
            Point(s +  4*u, s + 13*u), Point(s +  1*u, s + 16*u), Point(s +  3*u, t - 13*u), Point(s +  5*u, t -  4*u),
            Point(s + 10*u, t -  1*u), Point(s + 14*u, t - 15*u), Point(s + 18*u, s +  8*u)]
            
    edges = [(0,1), (1,2), (2,3), (3,4), (4,5), (5,6), (6,7), (7,8), (8,9), (9,10), (10,11), (11,12), (12,13), (13,14),
            (14,15), (15,16), (16,0), (1,3), (4,16), (4,17), (12,17), (14,17), (5,11), (6,18), (10,18)]

    dcel = DoublyConnectedEdgeList(points, edges)

    pl = PointLocation(Rectangle(Point(0, 0), Point(400, 400)), dcel)

    print("Success")

 
if __name__ == "__main__":
    main()
