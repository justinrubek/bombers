import logging
import pygame
import pygame.locals
import socket
import select
import random
import time

from util import WIDTH, HEIGHT

def getPos(string):
    x, sep, y = string.partition(',')
    return int(x), int(y)

def get_walls(string):
    walls = []
    
    for pos in string.split(';'):
        walls.append(getPos(pos))
        
    return walls

def get_explosion(string):
    explosion = []

    for pos in string.split(';'):
        explosion.append(getPos(pos))

    return explosion

class GameClient():
    def __init__(self, addr="127.0.0.1", serverport=3000):
        self.clientport = random.randrange(8000, 8999)
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind to localhost - set to external ip to connect from other computers
        self.conn.bind(("127.0.0.1", self.clientport))
        self.addr = addr
        self.serverport = serverport

        self.read_list = [self.conn]
        self.write_list = []

        self.setup_pygame()

    def setup_pygame(self, width=WIDTH, height=HEIGHT):
        self.screen = pygame.display.set_mode((width, height))
        self.bg_surface = pygame.image.load("bg.png").convert()

        # Load sprite images
        self.bombimage = pygame.image.load("bomb.png").convert_alpha() 
        self.explosionimage = pygame.image.load("explosion.png").convert_alpha() 
        self.playerimage = pygame.image.load("player.png").convert_alpha()
        self.wallimage = pygame.image.load("wall.png").convert_alpha() 

        pygame.event.set_allowed(None)
        pygame.event.set_allowed([pygame.locals.QUIT,
                                  pygame.locals.KEYDOWN])
        pygame.key.set_repeat(50, 50)

    def run(self):
        logging.debug("d")
        running = True
        clock = pygame.time.Clock()
        tickspeed = 30

        logging.debug("d")

        try:
            # Initialize connection to server
            self.conn.sendto(b"c", (self.addr, self.serverport))
            while running:
                clock.tick(tickspeed)

                readable, writable, exceptional = (
                    select.select(self.read_list, self.write_list, [], 0)
                )
                for conn in readable:
                    if conn is self.conn:
                        msg, addr = conn.recvfrom(1000000) # Grab a bunch of stuff if it is available
                        
                        # Draw the background
                        self.screen.blit(self.bg_surface, (0, 0))
                        
                        msg = msg.decode()
                        for data in msg.split('|'):
                            if len(data) == 0:
                                continue
                            msgtype = data[0]

                            data = data[1:]
                            if msgtype == "p":  # Player position
                                x, y = getPos(data)
                                
                                try:
                                    self.screen.blit(
                                        self.playerimage, (x, y))
                                except:
                                    # If something goes wrong, don't draw anything.
                                    pass
                            elif msgtype == "b":  # Bomb position
                                x, y = getPos(data)
                                
                                try:
                                    self.screen.blit(
                                        self.bombimage, (x, y))
                                except:
                                    # If something goes wrong, don't draw anything.
                                    pass
                                pass
                            elif msgtype == "e":  # Bomb explosion
                                explosion = get_explosion(data)
                                for pos in explosion:
                                    try:
                                        self.screen.blit(
                                            self.explosionimage, pos)
                                    except:
                                        # If something goes wrong, don't draw anything.
                                        pass
                            elif msgtype == "w": # Get the list of walls
                                walls = get_walls(data)
                                for wall in walls:
                                    self.screen.blit(
                                            self.wallimage, wall)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT or event.type == pygame.locals.QUIT:
                        running = False
                        break
                    elif event.type == pygame.locals.KEYDOWN:
                        if event.key == pygame.locals.K_w:
                            self.conn.sendto(
                                b"uu", (self.addr, self.serverport))
                        elif event.key == pygame.locals.K_s:
                            self.conn.sendto(
                                b"ud", (self.addr, self.serverport))
                        elif event.key == pygame.locals.K_a:
                            self.conn.sendto(
                                b"ul", (self.addr, self.serverport))
                        elif event.key == pygame.locals.K_d:
                            self.conn.sendto(
                                b"ur", (self.addr, self.serverport))
                        elif event.key == pygame.locals.K_SPACE:
                            self.conn.sendto(
                                b"b", (self.addr, self.serverport))
                        pygame.event.clear(pygame.locals.KEYDOWN)

                pygame.display.update()
        finally:
            self.conn.sendto(b"d", (self.addr, self.serverport))


if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s %(funcName)s: %(message)s on l%(lineno)d',
                        level=logging.DEBUG)
    g = GameClient()
    g.run()
