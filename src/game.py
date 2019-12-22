import pygame
from rpg.rogue import RPG

SURFACE_SIZE = (800, 600)
DUNGEON_SIZE = (255, 255)


def main():

    pygame.init()

    game = RPG(*SURFACE_SIZE)

    surface = pygame.display.set_mode(SURFACE_SIZE)
    pygame.display.set_caption("Rogue like RPG")

    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        game.update()
        surface.fill((0, 0, 0))
        game.render(surface)
        pygame.display.update()


if __name__ == '__main__':
    try:
        main()
    finally:
        pygame.quit()
