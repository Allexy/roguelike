from rpg.scene import MovableGameObject


class Monster(MovableGameObject):

    def __init__(self, x: int, y: int, type_id: int) -> None:
        self._x = x
        self._y = y
        self._type = type_id

    def position(self) -> tuple:
        return self._x, self._y

    def move(self, dx: int = 0, dy: int = 0) -> None:
        self._x += dx
        self._y += dy

    def type(self):
        return self._type
