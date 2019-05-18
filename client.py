import logging
import pygame
import pygame.locals
import socket
import select
import random
import time

def getPos(string):
    x, sep, y = string.partition(',')
    return int(x), int(y)


WIDTH = 1280
HEIGHT = 720

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

        self.playerimage = pygame.image.load("player.png").convert_alpha()
        self.bombimage = pygame.image.load("bomb.png").convert_alpha() 

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

                # select on specified file descriptors
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
                            msgtype = data[0]

                            if msgtype == "p":  # Player position
                                data = data[1:]
                                x, y = getPos(data)
                                
                                try:
                                    self.screen.blit(
                                        self.playerimage, (x, y))
                                except:
                                    # If something goes wrong, don't draw anything.
                                    pass
                            elif msgtype == "b":  # Bomb position
                                data = data[1:]
                                x, y = getPos(data)
                                
                                try:
                                    self.screen.blit(
                                        self.bombimage, (x, y))
                                except:
                                    # If something goes wrong, don't draw anything.
                                    pass
                                pass
                            elif msgtype == "e":  # Bomb explosion
                                pass

                for event in pygame.event.get():
                    if event.type == pygame.QUIT or event.type == pygame.locals.QUIT:
                        running = False
                        break
                    elif event.type == pygame.locals.KEYDOWN:
                        if event.key == pygame.locals.K_UP:
                            self.conn.sendto(
                                b"uu", (self.addr, self.serverport))
                        elif event.key == pygame.locals.K_DOWN:
                            self.conn.sendto(
                                b"ud", (self.addr, self.serverport))
                        elif event.key == pygame.locals.K_LEFT:
                            self.conn.sendto(
                                b"ul", (self.addr, self.serverport))
                        elif event.key == pygame.locals.K_RIGHT:
                            self.conn.sendto(
                                b"ur", (self.addr, self.serverport))
                        elif event.key == pygame.locals.K_b:
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
