import os
import pygame

BLOCK_SIZE = 64
WIDTH = 1024
HEIGHT = 568+32

# Width/Height of screen - size of sprite
X_MAX = WIDTH-BLOCK_SIZE 
Y_MAX = HEIGHT-BLOCK_SIZE

def load_image(name):
    fullname = os.path.abspath(name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error:
        print('Cannot load image:', fullname)
        raise SystemExit(str(geterror()))
        
    return image, image.get_rect()

def in_bounds(pos):
   return 0 <= pos[0] < X_MAX and 0 <= pos[1] < Y_MAX 

