from notebooks.modules.data_structures import DoublyConnectedEdgeList
from notebooks.modules.geometry import Point

def main():
    c = 0.5 * 64
    r = c
    s = c - r
    t = c + r
    u = (t - s) / 32
    u = 1
    points = [Point(s + 20*u, t), Point(s + 26*u, t -  6*u), Point(s + 30*u, t -  8*u), Point(s + 28*u, t - 10*u)]
    edges = [(1,2), (2,3), (2,4)]
    dcel = DoublyConnectedEdgeList(points, edges)
    for vertex in dcel.vertices():
        print(vertex.edge)

if __name__ == "__main__":
    main()
