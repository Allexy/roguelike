from pygame import Surface
from rpg.scene import SceneObject
from rpg.scene_progress import SceneProgress


class RPG(SceneObject):

    def __init__(self, w: int, h: int) -> None:
        self._scene = SceneProgress(w, h)

    def update(self) -> None:
        if self._scene.is_finished():
            next_scene = self._scene.next_scene()
            if next_scene is not None:
                self._scene = next_scene
        self._scene.update()

    def render(self, surface: Surface) -> None:
        self._scene.render(surface)
