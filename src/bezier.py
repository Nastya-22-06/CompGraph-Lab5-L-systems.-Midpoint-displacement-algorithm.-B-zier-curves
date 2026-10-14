"""Составная кубическая кривая Безье из одних опорных точек."""
from __future__ import annotations

Point = tuple[float, float]


def controls(points: list[Point], tension: float = 1.0):
    """Касательные вычисляются из соседних точек, а не правятся вручную.

    Преобразование интерполирующего Catmull–Rom в кубические сегменты Безье.
    """
    result = []
    for i in range(len(points)-1):
        p0 = points[max(0, i-1)]
        p1 = points[i]
        p2 = points[i+1]
        p3 = points[min(len(points)-1, i+2)]
        c1 = (p1[0]+(p2[0]-p0[0])*tension/6,
              p1[1]+(p2[1]-p0[1])*tension/6)
        c2 = (p2[0]-(p3[0]-p1[0])*tension/6,
              p2[1]-(p3[1]-p1[1])*tension/6)
        result.append((p1, c1, c2, p2))
    return result


def cubic(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    u = 1-t
    return (u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
            u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1])


def sample(points: list[Point], resolution: int = 30) -> list[Point]:
    curve = []
    for segment in controls(points):
        curve.extend(cubic(*segment, j/resolution) for j in range(resolution))
    if len(points) >= 2:
        curve.append(points[-1])
    return curve
