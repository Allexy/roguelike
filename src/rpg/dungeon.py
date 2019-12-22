from __future__ import annotations
import random
from typing import Callable
from heapq import heappush as push, heappop as pop

from rpg.utils import Point, Grid, Rect


class PathNotFoundError(RuntimeError):
    pass


class PathFinder:

    class PriorityQueue:

        class Item:

            def __init__(self, point: tuple, priority: int):
                self.point = point
                self.priority = priority

            def __lt__(self, other: PathFinder.PriorityQueue.Item):
                return self.priority < other.priority

        def __init__(self):
            self.items = []

        def is_empty(self) -> bool:
            return len(self.items) == 0

        def put(self, point: tuple, priority: int) -> None:
            push(self.items, PathFinder.PriorityQueue.Item(point, priority))

        def get(self) -> tuple:
            return pop(self.items).point

    def __init__(self, grid: Grid, cost: Callable[[tuple], int]):
        self._data = grid
        self._cost_callable = cost

    def cost(self, point_to: tuple, point_goal: tuple) -> int:
        dist = Point.dst(*point_to, *point_goal)
        return dist + self._cost_callable(point_to)

    def find(self, start: tuple, goal: tuple, allowed: set) -> list:
        frontier = PathFinder.PriorityQueue()
        frontier.put(start, 0)
        came_from = dict()
        came_from[start] = None
        cost_so_far = dict()
        cost_so_far[start] = 1
        while not frontier.is_empty():
            current = frontier.get()
            # check if goal is reached
            if current == goal:
                path = list()
                path.append(start)
                while current != start:
                    path.append(current)
                    current = came_from[current]
                return path
            for _next in self._data.neighbours(*current, allowed=allowed):
                new_cost = cost_so_far[current] + self.cost(_next, goal)
                if _next not in cost_so_far or new_cost < cost_so_far[_next]:
                    cost_so_far[_next] = new_cost
                    frontier.put(_next, new_cost)
                    came_from[_next] = current
        raise PathNotFoundError("Path not found")


class Room(Rect):

    def priority(self):
        return self._y * self._x


class _Generator:
    NUMBER_OF_ROOMS = 10
    MIN_ROOM_SIZE = 8
    MAX_ROOM_SIZE = 16
    MIN_DISTANCE_BETWEEN_ROOMS = 8
    TILE_CAVE = -1
    TILE_GROUND = 0
    TILE_CORRIDOR = 1
    TILE_FLOOR = 3
    TILE_DOOR = 4
    TILE_WALL_H = 5
    TILE_WALL_V = 6
    TILE_WALL_TL = 7
    TILE_WALL_TR = 8
    TILE_WALL_BL = 9
    TILE_WALL_BR = 10

    COST_CAVES_ALLOWED = {TILE_CAVE, TILE_GROUND}
    NEED_CONNECT_ALLOWED = {TILE_GROUND}
    CONNECT_CAVES_ALLOWED = {TILE_GROUND, TILE_CAVE}
    COST_ROOMS_ALLOWED = {TILE_CORRIDOR, TILE_GROUND, TILE_WALL_H, TILE_WALL_V, TILE_FLOOR, TILE_DOOR,
                          TILE_WALL_TL, TILE_WALL_BL, TILE_WALL_BR, TILE_WALL_TR}
    CONNECT_ROOMS_ALLOWED = {TILE_GROUND, TILE_WALL_H, TILE_WALL_V, TILE_FLOOR, TILE_CORRIDOR, TILE_DOOR}
    CLEAN_UP_ALLOWED = {TILE_CORRIDOR}

    def __init__(self, width: int, height: int, progress: Callable[[int], None] = None) -> None:
        self._width = width
        self._height = height
        self._data = Grid(width, height, init_value=_Generator.TILE_CAVE)
        self._progress_callback = progress
        self._rooms = list()

    def _random_room(self) -> Room:
        size = random.randrange(_Generator.MIN_ROOM_SIZE, _Generator.MAX_ROOM_SIZE)
        if size % 4:
            room_height = size
            room_width = size // 3 * 4
        else:
            room_width = size
            room_height = size // 3 * 4
        x = random.randrange(0, self._width - room_width)
        y = random.randrange(0, self._height - room_height)
        return Room(x, y, room_width, room_height)

    def _generate_room(self) -> Room:
        while True:
            new_room = self._random_room()
            for room in self._rooms:
                if room.intersects(new_room, min_distance=_Generator.MIN_DISTANCE_BETWEEN_ROOMS):
                    break
            else:
                return new_room

    def _drunk_man(self, x: int, y: int, depth: int = 5) -> None:
        if not self._data.in_bounds(x, y):
            return
        for _ in range(0, depth):
            select = random.randrange(0, 4)
            if select == 0 and y > 0:  # up
                y -= 1
            elif select == 1 and x < self._width - 1:  # right
                x += 1
            elif select == 2 and y < self._height - 1:  # down
                y += 1
            elif select == 3 and x > 0:  # left
                x -= 1
            for dx, dy in self._data.neighbours(x, y, allowed={_Generator.TILE_CAVE}):
                if self._data.get(dx, dy) == _Generator.TILE_CAVE:
                    self._data.put(dx, dy, _Generator.TILE_GROUND)

    def _cost_caves(self, to: tuple) -> int:
        weight = 0
        for x, y in self._data.neighbours(*to, allowed=_Generator.COST_CAVES_ALLOWED, diagonals=True):
            neighbour_type = self._data.get(x, y)
            if neighbour_type == _Generator.TILE_CAVE:
                weight += 1
            elif neighbour_type == _Generator.TILE_GROUND:
                weight += 10  # in order to make more ways

        return weight

    def _connect_pair_caves(self, a: Room, b: Room) -> None:
        path_finder = PathFinder(self._data, self._cost_caves)
        try:
            path = path_finder.find(a.center(), b.center(), allowed=_Generator.CONNECT_CAVES_ALLOWED)
            for ptr in path:
                for x, y in self._data.neighbours(*ptr, allowed=_Generator.CONNECT_CAVES_ALLOWED, diagonals=True):
                    if self._data.get(x, y) == _Generator.TILE_CAVE:
                        self._data.put(x, y, _Generator.TILE_CORRIDOR)
            for ptr in path:
                self._drunk_man(*ptr, depth=random.randrange(2, 4))
        except PathNotFoundError:
            pass

    def _connect_all_caves(self) -> None:
        for a, b in zip(self._rooms, self._rooms[1:]):
            self._connect_pair_caves(a, b)

    def _generate_caves(self) -> None:
        for room in self._rooms:
            (left, top, right, bottom) = room.bounds()
            for cx in range(left, right + 1):
                for cy in range(top, bottom + 1):
                    self._drunk_man(cx, cy, depth=random.randrange(4, 7))

    def _cost_rooms(self, to: tuple) -> int:
        weight = 0
        for x, y in self._data.neighbours(*to, allowed=_Generator.COST_ROOMS_ALLOWED, diagonals=True):
            neighbour_type = self._data.get(x, y)
            if neighbour_type == _Generator.TILE_GROUND:
                weight += 5
            elif neighbour_type == _Generator.TILE_FLOOR:
                weight += 1
            elif neighbour_type == _Generator.TILE_WALL_H or neighbour_type == _Generator.TILE_WALL_V:
                weight += 50
            elif neighbour_type == _Generator.TILE_WALL_TL or neighbour_type == _Generator.TILE_WALL_BL:
                weight += 70
            elif neighbour_type == _Generator.TILE_WALL_BR or neighbour_type == _Generator.TILE_WALL_TR:
                weight += 70
            elif neighbour_type == _Generator.TILE_CORRIDOR:
                weight += 1
            elif neighbour_type == _Generator.TILE_DOOR:
                weight += 1
            elif neighbour_type == _Generator.TILE_CAVE:
                weight += 10
        return weight

    def _connect_pair_rooms(self, a: Room, b: Room) -> None:
        path_finder = PathFinder(self._data, self._cost_rooms)
        try:
            for ptr in path_finder.find(a.center(), b.center(), allowed=_Generator.CONNECT_ROOMS_ALLOWED):
                cell_type = self._data.get(*ptr)
                if cell_type == _Generator.TILE_WALL_H or cell_type == _Generator.TILE_WALL_V:
                    self._data.put(*ptr, _Generator.TILE_DOOR)
                elif cell_type == _Generator.TILE_GROUND:
                    self._data.put(*ptr, _Generator.TILE_CORRIDOR)
        except PathNotFoundError:
            pass

    def _connect_all_rooms(self) -> None:
        for a, b in zip(self._rooms, self._rooms[1:]):
            self._connect_pair_rooms(a, b)

    def _clean_up(self) -> None:
        for x in range(1, self._width - 1):
            for y in range(1, self._height - 1):
                if self._data.get(x, y) == _Generator.TILE_CAVE:
                    for nx, ny in self._data.neighbours(x, y, allowed=_Generator.CLEAN_UP_ALLOWED, diagonals=True):
                        self._data.put(nx, ny, _Generator.TILE_GROUND)

    def _progress(self, progress: int):
        if self._progress_callback is not None:
            self._progress_callback(progress)

    def _copy_room_data(self, room: Room) -> None:
        (x1, y1, x2, y2) = room.bounds()
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                if x == x1 and y == y1:
                    self._data.put(x, y, _Generator.TILE_WALL_TL)
                elif x == x1 and y == y2:
                    self._data.put(x, y, _Generator.TILE_WALL_BL)
                elif x == x2 and y == y1:
                    self._data.put(x, y, _Generator.TILE_WALL_TR)
                elif x == x2 and y == y2:
                    self._data.put(x, y, _Generator.TILE_WALL_BR)
                elif y == y1 or y == y2:
                    self._data.put(x, y, _Generator.TILE_WALL_H)
                elif x == x1 or x == x2:
                    self._data.put(x, y, _Generator.TILE_WALL_V)
                else:
                    self._data.put(x, y, _Generator.TILE_FLOOR)

    def run(self) -> None:
        while len(self._rooms) < _Generator.NUMBER_OF_ROOMS:
            self._rooms.append(self._generate_room())
        self._progress(10)
        self._rooms.sort(key=lambda x: x.priority())
        self._generate_caves()
        self._progress(30)
        self._connect_all_caves()
        self._progress(50)
        for room in self._rooms:
            self._copy_room_data(room)
        self._connect_all_rooms()
        self._progress(70)
        self._clean_up()
        self._progress(100)

    def data(self) -> Grid:
        return self._data

    def rooms(self):
        return self._rooms


class Dungeon:
    STOP_TILES = {
        _Generator.TILE_DOOR,
        _Generator.TILE_CAVE,
        _Generator.TILE_WALL_TL,
        _Generator.TILE_WALL_TR,
        _Generator.TILE_WALL_BR,
        _Generator.TILE_WALL_BL,
        _Generator.TILE_WALL_H,
        _Generator.TILE_WALL_V,
    }

    def __init__(self, width: int, height: int, progress: Callable[[int], None] = None):
        generator = _Generator(width, height, progress)
        generator.run()
        self._data = generator.data()
        self._rooms = generator.rooms()
        self._hero_position = Point(*self._rooms[0].center())

    def area(self, area: Rect) -> Grid:
        return self._data.copy(*area.bounds())

    def hero_position(self) -> Point:
        return self._hero_position

    def width(self) -> int:
        return self._data.width()

    def height(self) -> int:
        return self._data.height()

    def get(self, x: int, y: int) -> int:
        return self._data.get(x, y)

    def is_movement_possible(self, x: int, y: int, dx: int, dy: int) -> bool:
        new_x = x + dx
        new_y = y + dy
        if not self._data.in_bounds(new_x, new_y):
            return False
        cell_type = self._data.get(new_x, new_y)
        return cell_type in (
            _Generator.TILE_DOOR,
            _Generator.TILE_CORRIDOR,
            _Generator.TILE_FLOOR,
            _Generator.TILE_GROUND
        )


if __name__ == '__main__':
    gen = Dungeon(128, 128)
    data = gen.area(Rect(0, 0, 128, 128))
    for row in data:
        for char in row:
            if char == _Generator.TILE_WALL_H or char == _Generator.TILE_WALL_V:
                print('##', sep='', end='')
            elif char == _Generator.TILE_FLOOR:
                print('++', sep='', end='')
            elif char == _Generator.TILE_CORRIDOR:
                print('[]', sep='', end='')
            elif char == _Generator.TILE_DOOR:
                print('HH', sep='', end='')
            elif char == _Generator.TILE_CAVE:
                print('CC', sep='', end='')
            else:
                print('..', sep='', end='')
        print('')
