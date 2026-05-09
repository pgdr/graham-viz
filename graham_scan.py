r"""The Graham scan algorithm for computing the convex hull.

Computes the convex hull of a set of $n$ points in the plane.  It runs in time
$O(n \log n)$, which is optimal.

"""

from dataclasses import dataclass


@dataclass(frozen=True, eq=True)
class Point:
    x: float
    y: float
    idx: float

    @property
    def tuple(self):
        return self.x, self.y

    def __lt__(self, other):
        return (self.x, self.y) < (
            other.x,
            other.y,
        )

    def __sub__(self, other):
        return Point(self.x - other.x, self.y - other.y, -1)

    @classmethod
    def from_str(c, s):
        return Point(*map(float, s.split()))


def cross(o, a, b):
    return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)


def right(a, b, c):
    return cross(a, b, c) <= 0


def graham(points):
    points = sorted(set(points))
    S, hull = [], []  # S is a stack of points

    for p in points:
        while len(S) >= 2 and right(S[-2], S[-1], p):
            S.pop()
        S.append(p)
    hull += S

    S = []
    for p in reversed(points):
        while len(S) >= 2 and right(S[-2], S[-1], p):
            S.pop()
        S.append(p)
    hull += S[1:-1]  # ignore endpoints
    return hull
