from __future__ import annotations
from math import isqrt
from typing import Any


class Point:

    def __init__(self, x: int = 0, y: int = 0, another: Point = None):
        if another is not None:
            self._x = another.x
            self._y = another.y
        else:
            self._x = x
            self._y = y

    def tup(self) -> tuple:
        return self.x, self.y

    @property
    def x(self) -> int:
        return self._x

    @x.setter
    def x(self, x: int) -> None:
        self._x = x

    @property
    def y(self) -> int:
        return self._y

    @y.setter
    def y(self, y: int) -> None:
        self._y = y

    @staticmethod
    def dst(x1: int, y1: int, x2: int, y2: int):
        return isqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    def distance(self, x: int = 0, y: int = 0, another: Point = None) -> int:
        if another is not None:
            return Point.dst(self._x, another.x, self._y, another.y)
        return Point.dst(self._x, x, self._y, y)

    def __eq__(self, other: Any) -> bool:
        if type(other) != Point:
            return False
        return other.x == self.x and other.y == self.y

    def __ne__(self, other: Any) -> bool:
        if type(other) != Point:
            return True
        return other.x != self.x or other.y != self.y

    def __hash__(self) -> int:
        return self._x * 1_000_000 + self._y


class Bounded:

    def bounds(self) -> tuple:
        pass

    def in_bounds(self, x: int, y: int) -> bool:
        pass


class Rect(Bounded):

    def __init__(self, x: int, y: int, width: int, height: int):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def bounds(self) -> tuple:
        return self._x, self._y, self._x + self._width, self._y + self._height

    def in_bounds(self, x: int, y: int) -> bool:
        return self._x <= x < self._x + self._width and self._y <= y < self._y + self._height

    def intersects(self, another: Bounded, min_distance: int = 0) -> bool:
        (left1, top1, right1, bottom1) = self.bounds()
        (left2, top2, right2, bottom2) = another.bounds()
        return left1 - min_distance <= right2 and \
            left2 <= right1 + min_distance and \
            top1 - min_distance <= bottom2 and \
            top2 <= bottom1 + min_distance

    def center(self) -> tuple:
        return self._x + self._width // 2, self._y + self._height // 2

    def position(self) -> tuple:
        return self._x, self._y


class Grid(Bounded):

    def __init__(self, width: int, height: int, init_value: int = 0, data: list = None) -> None:
        self._width = width
        self._height = height
        if data is None:
            self._data = [[init_value for _ in range(self._width)] for _ in range(self._height)]
        else:
            self._data = data

    def bounds(self) -> tuple:
        return 0, 0, self._width, self._height

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self._width and 0 <= y < self._height

    def put(self, x: int, y: int, val: int) -> None:
        if not self.in_bounds(x, y):
            raise ValueError("Coordinates ({},{}) are out of bounds".format(x, y))
        self._data[y][x] = val

    def get(self, x: int, y: int) -> int:
        if not self.in_bounds(x, y):
            raise ValueError("Coordinates ({},{}) are out of bounds".format(x, y))
        return self._data[y][x]

    def neighbours(self, x: int, y: int, allowed: set, diagonals: bool = False) -> list:
        if not self.in_bounds(x, y):
            raise ValueError("Coordinates ({},{}) are out of bounds".format(x, y))
        result = []
        if y - 1 > -1 and self._data[y - 1][x] in allowed:
            result.append((x, y - 1))
        if x + 1 < self._width and self._data[y][x + 1] in allowed:
            result.append((x + 1, y))
        if y + 1 < self._height and self._data[y + 1][x] in allowed:
            result.append((x, y + 1))
        if x - 1 > -1 and self._data[y][x - 1] in allowed:
            result.append((x - 1, y))
        if diagonals:
            if y - 1 > -1 and x - 1 > -1 and self._data[y - 1][x - 1] in allowed:
                result.append((x - 1, y - 1))
            if y - 1 > -1 and x + 1 < self._width and self._data[y - 1][x + 1] in allowed:
                result.append((x + 1, y - 1))
            if y + 1 < self._height and x + 1 < self._width and self._data[y + 1][x + 1] in allowed:
                result.append((x + 1, y + 1))
            if y + 1 < self._height and x - 1 > -1 and self._data[y + 1][x - 1] in allowed:
                result.append((x - 1, y + 1))
        return result

    def copy(self, left: int, top: int, right: int, bottom: int) -> Grid:
        left, top = max(left, 0), max(top, 0)
        right, bottom = min(right, self._width), min(bottom, self._height)
        width, height = right - left, bottom - top
        return Grid(width, height, data=[[self._data[y][x] for x in range(left, right)] for y in range(top, bottom)])

    def width(self):
        return self._width

    def height(self):
        return self._height

    def __iter__(self):
        self._iter = iter(self._data)
        return self

    def __next__(self):
        return next(self._iter)
