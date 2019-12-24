from __future__ import annotations
from pygame import Surface, image, BLEND_RGBA_SUB


class SceneObject:

    def update(self) -> None:
        pass

    def render(self, surface: Surface) -> None:
        pass


class AbstractScene(SceneObject):

    def is_finished(self) -> bool:
        pass

    def next_scene(self) -> AbstractScene:
        pass


class SpriteSheet:
    IMAGE = image.load("art/spritesheet.png")

    def __init__(self, tile_width: int = 16, tile_height: int = 16):
        self._tile_width = tile_width
        self._tile_height = tile_height

    def tile_width(self) -> int:
        return self._tile_width

    def tile_height(self) -> int:
        return self._tile_height

    def draw(self, surface: Surface, tile_row: int, tile_col: int, x: int, y: int, brightness: float = 1.0) -> None:
        _brightness = int(round(brightness * 1000.0))
        if _brightness == 0:
            return
        dst = (x * self._tile_width, y * self._tile_height, self._tile_width, self._tile_height)
        src = (self._tile_width * tile_col, self._tile_height * tile_row, self._tile_width, self._tile_height)
        # draw tile
        surface.blit(SpriteSheet.IMAGE, dst, src)
        if _brightness != 1000:
            # apply color mask
            color_level = 255 - int(round(255.0 * brightness))
            if color_level < 0:
                color_level = 0
            color_mask = (color_level, color_level, color_level, 0)
            surface.fill(color_mask, dst, special_flags=BLEND_RGBA_SUB)
