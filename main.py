import pygame
import config
from game import Game

if __name__ == "__main__":
    pygame.init()
    game = Game()
    game.run()
    pygame.quit()