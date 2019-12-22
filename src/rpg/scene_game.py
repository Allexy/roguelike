from pygame import Surface, key, K_LEFT, K_RIGHT, K_UP, K_DOWN, time
from rpg.scene import AbstractScene, SpriteSheet
from rpg.dungeon import Dungeon
from rpg.obj_hero import Hero
from rpg.utils import Rect, Point
from rpg.dungeon import _Generator


class SceneGame(AbstractScene):

    def __init__(self, dungeon: Dungeon, width: int, height: int):
        self._dungeon = dungeon
        self._hero = Hero(dungeon.hero_position())
        self._width = width
        self._height = height
        self._sprites = SpriteSheet()
        self._clock = time.Clock()

    def is_finished(self) -> bool:
        return False

    def next_scene(self) -> AbstractScene:
        raise NotImplemented

    def update(self) -> None:
        super().update()

        self._clock.tick(10)

        hero_dx, hero_dy = 0, 0
        pressed_keys = key.get_pressed()
        if pressed_keys[K_LEFT]:
            hero_dx = -1
        if pressed_keys[K_RIGHT]:
            hero_dx = 1
        if pressed_keys[K_UP]:
            hero_dy = -1
        if pressed_keys[K_DOWN]:
            hero_dy = 1

        if self._dungeon.is_movement_possible(*self._hero.position(), dx=hero_dx, dy=hero_dy):
            self._hero.move(hero_dx, hero_dy)

    def render(self, surface: Surface) -> None:
        super().render(surface)
        self._render_map(surface, *self._hero.position())

    def _render_map(self, surface: Surface, hero_x: int, hero_y: int):
        width = self._width // self._sprites.tile_width()
        height = self._height // self._sprites.tile_height()

        start_x = max(0, hero_x - width // 2)
        if start_x + width > self._dungeon.width():
            start_x -= (start_x + width - self._dungeon.width())

        start_y = max(0, hero_y - height // 2)
        if start_y + height > self._dungeon.height():
            start_y -= (start_y + height - self._dungeon.height())

        map_area = self._dungeon.area(Rect(start_x, start_y, width, height))
        for y, row in enumerate(map_area):
            for x, cell in enumerate(row):
                real_x, real_y = start_x + x, start_y + y
                brightness = self._calc_tile_brightness(real_x, real_y, hero_x, hero_y)
                # rendering map tiles
                if cell == _Generator.TILE_FLOOR:
                    self._sprites.draw(surface, 2, 0, x, y, brightness)
                elif cell == _Generator.TILE_CORRIDOR:
                    self._sprites.draw(surface, 2, 1, x, y, brightness)
                elif cell == _Generator.TILE_WALL_H:
                    self._sprites.draw(surface, 1, 2, x, y, brightness)
                elif cell == _Generator.TILE_WALL_V:
                    self._sprites.draw(surface, 0, 2, x, y, brightness)
                elif cell == _Generator.TILE_WALL_TL:
                    self._sprites.draw(surface, 0, 0, x, y, brightness)
                elif cell == _Generator.TILE_WALL_TR:
                    self._sprites.draw(surface, 0, 1, x, y, brightness)
                elif cell == _Generator.TILE_WALL_BR:
                    self._sprites.draw(surface, 1, 1, x, y, brightness)
                elif cell == _Generator.TILE_WALL_BL:
                    self._sprites.draw(surface, 1, 0, x, y, brightness)
                elif cell == _Generator.TILE_DOOR:
                    self._sprites.draw(surface, 2, 3, x, y, brightness)
                elif cell == _Generator.TILE_CAVE:
                    self._sprites.draw(surface, 2, 2, x, y, brightness)
                # render map objects
                self._render_map_objects(real_x, real_y, x, y, brightness)
                # render hero
                if real_x == hero_x and real_y == hero_y:
                    self._sprites.draw(surface, 0, 4, x, y, 1.0)

    def _render_map_objects(self, real_x: int, real_y: int, draw_x: int, draw_y: int, brightness: float) -> None:
        pass

    def _calc_tile_brightness(self, real_x: int, real_y: int, hero_x: int, hero_y: int) -> float:
        # Ray cast from hero to point
        dx = real_x - hero_x
        dy = real_y - hero_y
        mx = max(abs(dx), abs(dy))
        if mx == 0:
            return 1.0

        brightness = self._calc_distance_brightness(Point.dst(hero_x, hero_y, real_x, real_y))

        vec = (dx / mx, dy / mx)
        x, y = float(hero_x), float(hero_y)
        row, col = 0, 0
        while col != real_x or row != real_y:
            x += vec[0]
            y += vec[1]
            row = int(round(y))
            col = int(round(x))
            if self._dungeon.get(col, row) in Dungeon.STOP_TILES:
                return brightness if col == real_x and row == real_y else 0.6

        return brightness

    def _calc_distance_brightness(self, distance: float) -> float:
        return 0.35 + 5.0 / distance
