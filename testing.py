from notebooks.modules.data_structures import DoublyConnectedEdgeList, DoublyConnectedSimplePolygon
from notebooks.modules.geometry import Point, PointReference, LineSegment
from notebooks.modules.data_structures import monotone_triangulation, recursive_triangulation
from notebooks.modules.data_structures.vertical_decomposition import PointLocation
from notebooks.modules.geometry import Rectangle

def main():
    """ Testing """

    #points = [Point(0,0), Point(2,0), Point(2,2), Point(0,2)]#, Point(4,2), Point(5,1), Point(6,4)]
    #edges = [(0,1), (1,2), (0,2), (3,0)]#, (4,5), (5,6), (6,0)]
    #
    #dcel = DoublyConnectedEdgeList(points, edges)
    #
    #for edge in dcel.edges():
    #    print(edge)
    #print("------")

    ls_list = [LineSegment(Point(2,6), Point(15,4)), LineSegment(Point(4,1), Point(7,3)), LineSegment(Point(12,2), Point(18,2))]
    pl = PointLocation(Rectangle(Point(0,0), Point(20,20)))

    for ls in ls_list:
        pl.insert(ls)

    print("hello")


if __name__ == "__main__":
    main()
