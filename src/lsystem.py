"""L-системы: чтение правил, развитие и черепашья геометрия."""
from __future__ import annotations
from dataclasses import dataclass
import math
import random
from pathlib import Path

MAX_SYMBOLS = 500_000


@dataclass(frozen=True)
class LSystem:
    axiom: str
    angle: float
    direction: float
    rules: dict[str, list[tuple[float, str]]]
    draw_symbols: str = "FG"


def load_system(path: str | Path) -> LSystem:
    raw_lines = [line.strip() for line in Path(path).read_text(encoding='utf-8-sig').splitlines()]
    draw_symbols = 'FG'
    for line in raw_lines:
        if line.lower().startswith('# draw:'):
            draw_symbols = line.split(':', 1)[1].strip()
    validate_draw_symbols(draw_symbols)
    lines = [line for line in raw_lines if line and not line.startswith('#')]
    if not lines:
        raise ValueError('Файл L-системы пуст')
    try:
        axiom, angle, direction = lines[0].rsplit(maxsplit=2)
        angle, direction = float(angle), float(direction)
    except ValueError as exc:
        raise ValueError('Первая строка: <аксиома> <угол> <направление>') from exc
    rules: dict[str, list[tuple[float, str]]] = {}
    for line in lines[1:]:
        if '->' not in line:
            raise ValueError(f'Неверное правило: {line}')
        lhs, rhs = (part.strip() for part in line.split('->', 1))
        if len(lhs) != 1:
            raise ValueError('Слева от -> должен быть один символ')
        weight = 1.0
        # Допускаются варианты: X -> 0.3: F[+X] и X -> F[+X].
        if ':' in rhs:
            prefix, tail = rhs.split(':', 1)
            try:
                weight = float(prefix.strip())
            except ValueError:
                pass
            else:
                rhs = tail.strip()
        if weight <= 0 or not math.isfinite(weight):
            raise ValueError('Вес правила должен быть положительным')
        rules.setdefault(lhs, []).append((weight, rhs))
    return LSystem(axiom, angle, direction, rules, draw_symbols)


def expand(system: LSystem, iterations: int, seed: int = 42) -> str:
    if not 0 <= iterations <= 12:
        raise ValueError('Число итераций: 0–12')
    rng = random.Random(seed)
    result = system.axiom
    for _ in range(iterations):
        parts = []
        for ch in result:
            variants = system.rules.get(ch)
            if not variants:
                parts.append(ch)
            elif len(variants) == 1:
                parts.append(variants[0][1])
            else:
                parts.append(rng.choices([v for _, v in variants],
                                         weights=[w for w, _ in variants])[0])
        result = ''.join(parts)
        if len(result) > MAX_SYMBOLS:
            raise ValueError('Слишком много символов: уменьшите число итераций')
    return result


@dataclass(frozen=True)
class Segment:
    x1: float
    y1: float
    x2: float
    y2: float
    depth: int = 0


def validate_draw_symbols(symbols: str) -> None:
    """Запрещаем конфликт с командами черепашки."""
    if not symbols or any(ch.isspace() or ch in "+-[]f" for ch in symbols):
        raise ValueError("Рисующие символы: непустая строка без + - [ ] f и пробелов")


def trace(commands: str, angle: float, direction: float, jitter: float = 0,
          seed: int = 42, draw_symbols: str = "FG") -> list[Segment]:
    """Символы draw_symbols рисуют; f перемещает; [] ветвят."""
    validate_draw_symbols(draw_symbols)
    if jitter < 0 or not math.isfinite(jitter):
        raise ValueError("Случайный угол должен быть неотрицательным числом")
    rng = random.Random(seed)
    x = y = 0.0
    heading = math.radians(direction)
    stack: list[tuple[float, float, float, int]] = []
    depth = 0
    segments = []
    for ch in commands:
        if ch in draw_symbols or ch == 'f':
            nx, ny = x + math.cos(heading), y + math.sin(heading)
            if ch in draw_symbols:
                segments.append(Segment(x, y, nx, ny, depth))
            x, y = nx, ny
        elif ch in '+-':
            delta = math.radians(angle + rng.uniform(-jitter, jitter))
            heading += delta if ch == '+' else -delta
        elif ch == '[':
            stack.append((x, y, heading, depth))
            depth += 1
        elif ch == ']':
            if not stack:
                raise ValueError('Лишняя закрывающая скобка ]')
            x, y, heading, depth = stack.pop()
    if stack:
        raise ValueError('Не закрыты квадратные скобки [')
    return segments


def fit_segments(segments: list[Segment], width: int, height: int,
                 padding: int = 30) -> list[Segment]:
    """Единый масштаб и центрирование с сохранением пропорций."""
    if not segments:
        return []
    xs = [p for s in segments for p in (s.x1, s.x2)]
    ys = [p for s in segments for p in (s.y1, s.y2)]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    scale = min(max(1, width-2*padding)/max(xmax-xmin, 1e-10),
                max(1, height-2*padding)/max(ymax-ymin, 1e-10))
    ox = (width - (xmax-xmin)*scale)/2
    oy = (height - (ymax-ymin)*scale)/2
    def point(x: float, y: float) -> tuple[float, float]:
        return ox+(x-xmin)*scale, height-(oy+(y-ymin)*scale)
    return [Segment(*point(s.x1, s.y1), *point(s.x2, s.y2), s.depth)
            for s in segments]
