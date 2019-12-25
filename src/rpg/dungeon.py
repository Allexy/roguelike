from __future__ import annotations
import random
from typing import Callable
from heapq import heappush as push, heappop as pop

from rpg.obj_loot import Loot
from rpg.obj_monsters import Monster
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


class Tiles:
    # tiles
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
    # objects
    OBJ_WEAPON = 0
    OBJ_ROD = 1
    OBJ_ARMOR = 2
    OBJ_RING = 3
    OBJ_FOOD = 4
    OBJ_POTION = 5
    OBJ_COINS = 6
    OBJ_SCROLL = 7
    # monsters
    MON_BAT = 0
    MON_SOMETHING = 1
    MON_CENTAUR = 2
    MON_HYDRA = 3
    MON_KIWI = 4
    MON_VENUS = 5
    MON_GRIFFIN = 6
    MON_TROLL = 7
    MON_GHOST = 8
    MON_DRAGON = 9
    MON_BLACK_BIRD = 10
    MON_LEPRECHAUN = 11
    MON_ZOMBIE_GIRL = 12

    SPRITE_TILE = {
        TILE_FLOOR: (2, 0),
        TILE_GROUND: (2, 5),
        TILE_CORRIDOR: (2, 1),
        TILE_WALL_H: (1, 2),
        TILE_WALL_V: (0, 2),
        TILE_WALL_TL: (0, 0),
        TILE_WALL_TR: (0, 1),
        TILE_WALL_BR: (1, 1),
        TILE_WALL_BL: (1, 0),
        TILE_DOOR: (2, 3),
        TILE_CAVE: (2, 2),
    }

    SPRITE_OBJECT = {
        OBJ_WEAPON: (0, 5),
        OBJ_ROD: (1, 5),
        OBJ_ARMOR: (0, 6),
        OBJ_RING: (1, 6),
        OBJ_FOOD: (0, 7),
        OBJ_POTION: (1, 7),
        OBJ_COINS: (1, 4),
        OBJ_SCROLL: (2, 4)
    }

    SPRITE_MONSTER = {
        MON_BAT: (3, 1),
        MON_SOMETHING: (3, 0),
        MON_CENTAUR: (3, 2),
        MON_HYDRA: (3, 3),
        MON_KIWI: (3, 4),
        MON_VENUS: (3, 5),
        MON_GRIFFIN: (3, 6),
        MON_TROLL: (3, 7),
        MON_GHOST: (3, 8),
        MON_DRAGON: (3, 9),
        MON_BLACK_BIRD: (3, 10),
        MON_LEPRECHAUN: (3, 11),
        MON_ZOMBIE_GIRL: (3, 12),
    }


class _Generator:
    NUMBER_OF_ROOMS = 10
    MIN_ROOM_SIZE = 8
    MAX_ROOM_SIZE = 16
    MIN_DISTANCE_BETWEEN_ROOMS = 8

    DRUNK_MAN_ALLOWED = {
        Tiles.TILE_CAVE
    }

    COST_CAVES_ALLOWED = {
        Tiles.TILE_CAVE,
        Tiles.TILE_GROUND
    }

    NEED_CONNECT_ALLOWED = {
        Tiles.TILE_GROUND
    }

    CONNECT_CAVES_ALLOWED = {
        Tiles.TILE_GROUND,
        Tiles.TILE_CAVE
    }

    COST_ROOMS_ALLOWED = {
        Tiles.TILE_CORRIDOR,
        Tiles.TILE_GROUND,
        Tiles.TILE_WALL_H,
        Tiles.TILE_WALL_V,
        Tiles.TILE_FLOOR,
        Tiles.TILE_DOOR,
        Tiles.TILE_WALL_TL,
        Tiles.TILE_WALL_BL,
        Tiles.TILE_WALL_BR,
        Tiles.TILE_WALL_TR
    }

    CONNECT_ROOMS_ALLOWED = {
        Tiles.TILE_GROUND,
        Tiles.TILE_WALL_H,
        Tiles.TILE_WALL_V,
        Tiles.TILE_FLOOR,
        Tiles.TILE_CORRIDOR,
        Tiles.TILE_DOOR
    }

    CLEAN_UP_ALLOWED = {
        Tiles.TILE_CORRIDOR
    }

    def __init__(self, width: int, height: int, progress: Callable[[int], None] = None) -> None:
        self._width = width
        self._height = height
        self._data = Grid(width, height, init_value=Tiles.TILE_CAVE)
        self._progress_callback = progress
        self._rooms = list()
        self._cave_nooks = list()

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

    def _drunk_man(self, start_x: int, start_y: int, depth: int = 5) -> tuple:
        if not self._data.in_bounds(start_x, start_y):
            return -1, -1, -1
        drunk_x, drunk_y = start_x, start_y
        nk_x, nk_y, nk_d = 0, 0, 0
        for _ in range(0, depth):
            select = random.randrange(0, 4)
            if select == 0 and drunk_y > 0:  # up
                drunk_y -= 1
            elif select == 1 and drunk_x < self._width - 1:  # right
                drunk_x += 1
            elif select == 2 and drunk_y < self._height - 1:  # down
                drunk_y += 1
            elif select == 3 and drunk_x > 0:  # left
                drunk_x -= 1
            for x, y in self._data.neighbours(drunk_x, drunk_y, allowed=_Generator.DRUNK_MAN_ALLOWED):
                self._data.put(x, y, Tiles.TILE_GROUND)
                d = Point.dst(x, y, start_x, start_y)
                if d > nk_d:
                    nk_d = d
                    nk_x = x
                    nk_y = y
        return nk_x, nk_y, nk_d

    def _cost_caves(self, to: tuple) -> int:
        weight = 0
        for x, y in self._data.neighbours(*to, allowed=_Generator.COST_CAVES_ALLOWED, diagonals=True):
            neighbour_type = self._data.get(x, y)
            if neighbour_type == Tiles.TILE_CAVE:
                weight += 1
            elif neighbour_type == Tiles.TILE_GROUND:
                weight += 10  # in order to make more ways

        return weight

    def _connect_pair_caves(self, a: Room, b: Room) -> None:
        path_finder = PathFinder(self._data, self._cost_caves)
        try:
            path = path_finder.find(a.center(), b.center(), allowed=_Generator.CONNECT_CAVES_ALLOWED)
            for ptr in path:
                for x, y in self._data.neighbours(*ptr, allowed=_Generator.CONNECT_CAVES_ALLOWED, diagonals=True):
                    if self._data.get(x, y) == Tiles.TILE_CAVE:
                        self._data.put(x, y, Tiles.TILE_CORRIDOR)
            for ptr in path:
                x, y, d = self._drunk_man(*ptr, depth=random.randrange(2, 5))
                if d >= 2:
                    self._cave_nooks.append(Point(x, y))

        except PathNotFoundError:
            pass

    def _connect_all_caves(self) -> None:
        for a, b in zip(self._rooms, self._rooms[1:]):
            self._connect_pair_caves(a, b)

    def _generate_caves(self) -> None:
        for room in self._rooms:
            left, top, right, bottom = room.bounds()
            center_x, center_y = room.center()
            distance = min(abs(center_x - left), abs(center_y - top)) + 1
            for cx in range(left, right + 1):
                for cy in range(top, bottom + 1):
                    x, y, _ = self._drunk_man(cx, cy, depth=random.randrange(4, 7))
                    d = Point.dst(x, y, center_x, center_y)
                    if d > distance and _ > 0 and x != left and x != right and y != top and y != bottom:
                        self._cave_nooks.append(Point(x, y))

    def _cost_rooms(self, to: tuple) -> int:
        weight = 0
        for x, y in self._data.neighbours(*to, allowed=_Generator.COST_ROOMS_ALLOWED, diagonals=True):
            neighbour_type = self._data.get(x, y)
            if neighbour_type == Tiles.TILE_GROUND:
                weight += 5
            elif neighbour_type == Tiles.TILE_FLOOR:
                weight += 1
            elif neighbour_type == Tiles.TILE_WALL_H or neighbour_type == Tiles.TILE_WALL_V:
                weight += 50
            elif neighbour_type == Tiles.TILE_WALL_TL or neighbour_type == Tiles.TILE_WALL_BL:
                weight += 70
            elif neighbour_type == Tiles.TILE_WALL_BR or neighbour_type == Tiles.TILE_WALL_TR:
                weight += 70
            elif neighbour_type == Tiles.TILE_CORRIDOR:
                weight += 1
            elif neighbour_type == Tiles.TILE_DOOR:
                weight += 1
            elif neighbour_type == Tiles.TILE_CAVE:
                weight += 10
        return weight

    def _connect_pair_rooms(self, a: Room, b: Room) -> None:
        path_finder = PathFinder(self._data, self._cost_rooms)
        try:
            for ptr in path_finder.find(a.center(), b.center(), allowed=_Generator.CONNECT_ROOMS_ALLOWED):
                cell_type = self._data.get(*ptr)
                if cell_type == Tiles.TILE_WALL_H or cell_type == Tiles.TILE_WALL_V:
                    self._data.put(*ptr, Tiles.TILE_DOOR)
                elif cell_type == Tiles.TILE_GROUND:
                    self._data.put(*ptr, Tiles.TILE_CORRIDOR)
        except PathNotFoundError:
            pass

    def _connect_all_rooms(self) -> None:
        for a, b in zip(self._rooms, self._rooms[1:]):
            self._connect_pair_rooms(a, b)

    def _clean_up(self) -> None:
        for x in range(1, self._width - 1):
            for y in range(1, self._height - 1):
                if self._data.get(x, y) == Tiles.TILE_CAVE:
                    for nx, ny in self._data.neighbours(x, y, allowed=_Generator.CLEAN_UP_ALLOWED, diagonals=True):
                        self._data.put(nx, ny, Tiles.TILE_GROUND)

    def _progress(self, progress: int):
        if self._progress_callback is not None:
            self._progress_callback(progress)

    def _copy_room_data(self, room: Room) -> None:
        (x1, y1, x2, y2) = room.bounds()
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                if x == x1 and y == y1:
                    self._data.put(x, y, Tiles.TILE_WALL_TL)
                elif x == x1 and y == y2:
                    self._data.put(x, y, Tiles.TILE_WALL_BL)
                elif x == x2 and y == y1:
                    self._data.put(x, y, Tiles.TILE_WALL_TR)
                elif x == x2 and y == y2:
                    self._data.put(x, y, Tiles.TILE_WALL_BR)
                elif y == y1 or y == y2:
                    self._data.put(x, y, Tiles.TILE_WALL_H)
                elif x == x1 or x == x2:
                    self._data.put(x, y, Tiles.TILE_WALL_V)
                else:
                    self._data.put(x, y, Tiles.TILE_FLOOR)

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

    def nooks(self):
        return self._cave_nooks


class Dungeon:
    # fog of war constants
    TILE_NOT_VISITED = 0
    TILE_VISITED = 1

    MOVEMENT_ALLOWED = (
        Tiles.TILE_DOOR,
        Tiles.TILE_CORRIDOR,
        Tiles.TILE_FLOOR,
        Tiles.TILE_GROUND
    )

    STOP_TILES = (
        Tiles.TILE_DOOR,
        Tiles.TILE_CAVE,
        Tiles.TILE_WALL_TL,
        Tiles.TILE_WALL_TR,
        Tiles.TILE_WALL_BR,
        Tiles.TILE_WALL_BL,
        Tiles.TILE_WALL_H,
        Tiles.TILE_WALL_V,
    )

    def __init__(self, width: int, height: int, progress: Callable[[int], None] = None):
        generator = _Generator(width, height, progress)
        generator.run()
        self._data = generator.data()
        self._fog_of_war = Grid(width, height, Dungeon.TILE_NOT_VISITED)
        self._rooms = generator.rooms()
        self._nooks = generator.nooks()
        self._objects = list()
        self._monsters = list()
        self._hero_position = Point(*self._rooms[0].center())
        self._place_objects()
        self.update_visible()

    def _place_objects(self) -> None:
        random_objects = [
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2,
            -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2,
            -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2, -2,
            Tiles.OBJ_FOOD, Tiles.OBJ_POTION, Tiles.OBJ_POTION, Tiles.OBJ_COINS, Tiles.OBJ_COINS,
        ]
        random_monsters = [
            Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_BAT,
            Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_BAT,
            Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_BAT, Tiles.MON_SOMETHING,
            Tiles.MON_CENTAUR, Tiles.MON_KIWI, Tiles.MON_VENUS, Tiles.MON_TROLL, Tiles.MON_GHOST,
            Tiles.MON_BLACK_BIRD, Tiles.MON_LEPRECHAUN, Tiles.MON_ZOMBIE_GIRL
        ]
        random.shuffle(random_objects)
        random.shuffle(random_monsters)
        for nook_point in self._nooks:
            random.shuffle(random_objects)  # shuffle twice:)
            obj_id = random.choice(random_objects)
            if obj_id < 0:
                if obj_id == -1:
                    self._monsters.append(Monster(*nook_point.tup(), random.choice(random_monsters)))
                continue
            self._objects.append(Loot(*nook_point.tup(), obj_id))
        room_monsters = [
            Tiles.MON_HYDRA, Tiles.MON_GRIFFIN, Tiles.MON_DRAGON, Tiles.MON_LEPRECHAUN,
            Tiles.MON_ZOMBIE_GIRL, Tiles.MON_CENTAUR
        ]
        room_objects = [
            Tiles.OBJ_WEAPON, Tiles.OBJ_ROD, Tiles.OBJ_ARMOR, Tiles.OBJ_RING, Tiles.OBJ_SCROLL,
            Tiles.OBJ_POTION, Tiles.OBJ_COINS, Tiles.OBJ_COINS
        ]
        random.shuffle(room_monsters)
        random.shuffle(room_objects)
        for room in self._rooms:
            l, t, r, b = room.bounds()
            if random.random() < 0.5:
                obj_id = random.choice(room_objects)
                rand_x = random.randrange(l+1, r-1)
                rand_y = random.randrange(t+1, b-1)
                self._objects.append(Loot(rand_x, rand_y, obj_id))

            if random.random() < 0.5:
                mon_id = random.choice(room_monsters)
                rand_x = random.randrange(l+1, r-1)
                rand_y = random.randrange(t+1, b-1)
                self._monsters.append(Monster(rand_x, rand_y, mon_id))

        del self._nooks
        del self._rooms

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
        if dx == 0 and dy == 0:  # None movement is impossible
            return False
        new_x = x + dx
        new_y = y + dy
        if not self._data.in_bounds(new_x, new_y):
            return False
        cell_type = self._data.get(new_x, new_y)
        return cell_type in Dungeon.MOVEMENT_ALLOWED

    def is_visited(self, x: int, y: int) -> bool:
        return self._fog_of_war.get(x, y) == Dungeon.TILE_VISITED

    def update_visible(self) -> None:
        dist = 7  # 14 solved eq. used for brightness function 0.25 + 4 / distance > 0.5
        start_x = max(0, self._hero_position.x - dist)
        start_y = max(0, self._hero_position.y - dist)
        end_x = min(self._fog_of_war.width(), self._hero_position.x + dist)
        end_y = min(self._fog_of_war.height(), self._hero_position.y + dist)
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                if self._hero_position.distance(x, y) <= dist:
                    self._fog_of_war.put(x, y, Dungeon.TILE_VISITED)

    def objects(self) -> list:
        return self._objects

    def monsters(self) -> list:
        return self._monsters


if __name__ == '__main__':
    gen = Dungeon(128, 128)
    data = gen.area(Rect(0, 0, 128, 128))
    for row in data:
        for char in row:
            if char == Tiles.TILE_WALL_H or char == Tiles.TILE_WALL_V:
                print('##', sep='', end='')
            elif char == Tiles.TILE_FLOOR:
                print('++', sep='', end='')
            elif char == Tiles.TILE_CORRIDOR:
                print('[]', sep='', end='')
            elif char == Tiles.TILE_DOOR:
                print('HH', sep='', end='')
            elif char == Tiles.TILE_CAVE:
                print('CC', sep='', end='')
            else:
                print('..', sep='', end='')
        print('')
