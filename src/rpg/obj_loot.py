from rpg.scene import GameObject


class Loot(GameObject):

    def __init__(self, x: int, y: int, type_id: int):
        self._x = x
        self._y = y
        self._type_id = type_id

    def position(self) -> tuple:
        return self._x, self._y

    def type(self) -> int:
        return self._type_id
