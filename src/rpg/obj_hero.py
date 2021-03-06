from rpg.scene import MovableGameObject
from rpg.utils import Point


class Hero(MovableGameObject):

    def __init__(self, position: Point):
        self._position = position

    def position(self) -> tuple:
        return self._position.tup()

    def move(self, dx: int = 0, dy: int = 0) -> None:
        self._position.x += dx
        self._position.y += dy
