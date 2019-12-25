import threading
from typing import Callable
from pygame import Surface, draw, font
from rpg.scene import AbstractScene
from rpg.dungeon import Dungeon
from rpg.scene_game import SceneGame


class SceneProgress(AbstractScene):
    PROGRESS_BAR_WIDTH = 100
    PROGRESS_BAR_HEIGHT = 16
    PROGRESS_BAR_BACKGROUND_COLOR = (0, 0, 255)
    PROGRESS_BAR_FOREGROUND_COLOR = (255, 0, 0)

    class BackgroundGeneration(threading.Thread):

        def __init__(self, progress: Callable[[int], None], data_ready: Callable[[Dungeon], None]):
            super().__init__()
            self._progress = progress
            self._ready = data_ready

        def run(self) -> None:
            self._ready(Dungeon(256, 256, self._progress))

    def __init__(self, width: int, height: int):
        super().__init__()
        self._width = width
        self._height = height
        self._progress = 0
        self._finished = False
        self._data = None
        self._font = font.Font('freesansbold.ttf', 10)
        thread = SceneProgress.BackgroundGeneration(self._generation_progress, self._create_next_scene)
        thread.start()

    def _create_next_scene(self, map_data: Dungeon):
        self._data = map_data
        self._finished = True

    def _generation_progress(self, progress: int):
        self._progress = progress

    def update(self) -> None:
        return

    def render(self, surface: Surface) -> None:
        left = self._width // 2 - SceneProgress.PROGRESS_BAR_WIDTH // 2
        top = self._height // 2 - SceneProgress.PROGRESS_BAR_HEIGHT // 2

        draw.rect(
            surface,
            SceneProgress.PROGRESS_BAR_BACKGROUND_COLOR,
            (left - 2, top - 2, SceneProgress.PROGRESS_BAR_WIDTH + 4, SceneProgress.PROGRESS_BAR_HEIGHT + 4)
        )

        draw.rect(
            surface,
            SceneProgress.PROGRESS_BAR_FOREGROUND_COLOR,
            (left, top, self._progress, SceneProgress.PROGRESS_BAR_HEIGHT)
        )

        text = self._font.render(
            "Generating: {}%".format(self._progress),
            True,
            SceneProgress.PROGRESS_BAR_BACKGROUND_COLOR
        )
        surface.blit(text, (left + 2, top + SceneProgress.PROGRESS_BAR_HEIGHT + 4))

    def is_finished(self) -> bool:
        return self._finished

    def next_scene(self) -> AbstractScene:
        return SceneGame(self._data, self._width, self._height)
