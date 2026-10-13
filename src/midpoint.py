"""Последовательные приближения горного профиля midpoint displacement."""
import random


def generate(steps: int = 8, amplitude: float = 0.25, roughness: float = 0.55,
             seed: int = 42, left: float = 0.35, right: float = 0.35):
    if not 0 <= steps <= 11:
        raise ValueError('Количество шагов должно быть от 0 до 11')
    if not 0 <= amplitude <= 2 or not 0 <= roughness <= 1:
        raise ValueError('Амплитуда: 0–2; roughness: 0–1')
    rng = random.Random(seed)
    points = [(0.0, left), (1.0, right)]
    history = [points.copy()]
    for level in range(steps):
        updated = [points[0]]
        displacement = amplitude * roughness**level
        for a, b in zip(points, points[1:]):
            midpoint = ((a[0]+b[0])/2, (a[1]+b[1])/2 + rng.uniform(-displacement, displacement))
            updated.extend((midpoint, b))
        points = updated
        history.append(points.copy())
    return history
