from notebooks.modules.data_structures import DoublyConnectedEdgeList, DoublyConnectedSimplePolygon
from notebooks.modules.geometry import Point, PointReference
from notebooks.modules.data_structures import monotone_triangulation, recursive_triangulation

def main():
    """ Testing """

    points = [Point(0,0), Point(2,0), Point(2,2), Point(0,2)]#, Point(4,2), Point(5,1), Point(6,4)]
    edges = [(0,1), (1,2), (0,2), (3,0)]#, (4,5), (5,6), (6,0)]

    dcel = DoublyConnectedEdgeList(points, edges)
    
    for edge in dcel.edges():
        print(edge)
    print("------")


if __name__ == "__main__":
    main()
