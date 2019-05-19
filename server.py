import os, random, socket, select, sys, time
import pygame
from pygame.locals import *

# Messages:
#  Client -> Server
#   First character is the command. Some commands have extra characters
#     b: drop bomb
#     c: connect
#     d: disconnect
#     u: update position -- Followed by direction {u,d,l,r}
#
#  Server -> Client
#   '|' delimited pairs of positions to draw the players (there is no
#     distinction between the players - not even the client knows where its
#     player is.

from util import BLOCK_SIZE, X_MAX, Y_MAX, load_image, in_bounds

class Bomb(pygame.sprite.Sprite):
    def __init__(self, pos, life=(3,5)):
        pygame.sprite.Sprite.__init__(self)
        _, self.rect = load_image("bomb.png")
        self.rect.topleft = pos
        
        self.life = random.randrange(*life)
        self.timestamp = time.time()

    def check_exploded(self):
        now = time.time()
        if now - self.timestamp >= self.life:
            return True
        return False
    
    def get_pos(self):
        return self.rect.topleft
    
    def collides_with(self, sprite):
        return self.rect.colliderect(sprite.rect)

    def primed(self):
        now = time.time()
        # See if it's been  a second since the bomb was placed
        return now - self.timestamp >= 1
        

class Wall(pygame.sprite.Sprite):
    def __init__(self, pos):
        pygame.sprite.Sprite.__init__(self)
        _, self.rect = load_image("wall.png")
        
        self.rect.topleft = pos
        self.timestamp = time.time()
    
    def get_pos(self):
        return self.rect.topleft
    
    def collides_with(self, sprite):
        return not self.rect.colliderect(sprite.rect)

class Player(pygame.sprite.Sprite):
    def __init__(self, pos, addr):
        pygame.sprite.Sprite.__init__(self)
        _, self.rect = load_image("player.png")

        self.addr = addr
        
        self.rect.topleft = pos
        self.alive = True

    def get_pos(self):
        return self.rect.topleft
        
    def get_move(self, vector):
        return self.rect.move(vector)

    def move(self, newrect):
        if in_bounds(newrect.topleft):
            self.rect = newrect

    def collides_with(self, sprite):
        print("S:{}".format(sprite))
        return not self.rect.colliderect(sprite.rect)

    def kill(self):
        self.alive = False
            
class Explosion(pygame.sprite.Sprite):
    def __init__(self, pos, life=1):
        pygame.sprite.Sprite.__init__(self)
        _, self.rect = load_image("explosion.png")
        
        self.rect.topleft = pos
        self.life = life
        self.timestamp = time.time()

        rects = []
        width = self.rect.width
        height = self.rect.height
        start = self.rect.topleft
        
        # Figure out which spaces this occupies, add to rects
        # Determine the length/height of the blast 
        options = [1, 2, 3, 4, 5, 6, 8]
        weights = [1, 5, 7, 6, 3, 2, 1]
        length_of_blast = random.choices(options, weights)[0]
        height_of_blast = random.choices(options, weights)[0]
        
        initialX = random.randrange(-(length_of_blast // 2), 1)
        initialY = random.randrange(-(height_of_blast // 2), 1)
        
        for i in range(initialX, length_of_blast):
            rect = pygame.Rect(start[0]+(BLOCK_SIZE*i), start[1], width, height) 
            print("R:{}".format(rect))
            rects.append(rect)
            
        for j in range(initialY, height_of_blast):
            rect = pygame.Rect(start[0], start[1]+(BLOCK_SIZE*j), width, height) 
            rects.append(rect)
       # rects.append(pygame.Rect(start[0]-BLOCK_SIZE, start[1], width, height))
       # rects.append(pygame.Rect(start[0]+BLOCK_SIZE, start[1], width, height))
        self.rects = rects

    def collides_with(self, sprite):
        print(type(sprite))
        for rect in self.rects:
            if rect.colliderect(sprite.rect):
                return True

        return False

    def check_over(self):
        now = time.time()
        if now - self.timestamp >= self.life:
            return True
        return False
    
    def get_pos(self):
        return self.rect.topleft

    def get_rects(self):
        return self.rects
        

class GameServer():
    def __init__(self, address="127.0.0.1", port=3000):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.listener.bind((address, port))
        self.read_list = [self.listener]
        self.write_list = []

        self.stepsize = 13
        self.players = {}
        self.bombs = []
        self.explosions = []

        self.walls = []
        
        for i in range(0, X_MAX // BLOCK_SIZE+1):
            x = i * BLOCK_SIZE 
            if x < BLOCK_SIZE:
                continue
            for j in range(0 , Y_MAX // BLOCK_SIZE+1):
                y = j * BLOCK_SIZE 
                if y < BLOCK_SIZE:
                    continue
                if i % 2 == 1 and j % 2 == 1:
                    self.walls.append(Wall((x, y)))

    def handle_movement(self, mv, player):
        player = self.players[player]
        if player.alive == False:
            return
        
        pos = player.get_pos()
        move = None
        if mv == "u":
            move = player.get_move((0, -self.stepsize))
        elif mv == "d":
            move = player.get_move((0, self.stepsize))
        elif mv == "l":
            move = player.get_move((-self.stepsize, 0))
        elif mv == "r":
            move = player.get_move((self.stepsize, 0))

        for wall in self.walls:
            # check collision between player and wall
            if move.colliderect(wall.rect):
                print("{} collides with player {}".format(wall.get_pos(), player.rect.bottomright))
                return
            
        for bomb in self.bombs:
            # check collision between player and wall
            if bomb.primed():
                if move.colliderect(bomb.rect):
                    print("{} collides with player {}".format(bomb.get_pos(), player.rect.bottomright))
                    return
            
        player.move(move)

    def add_bomb(self, player):
        # Find the position of the player
        pos = self.players[player].get_pos()
        self.bombs.append(Bomb(pos))
        print("Placed bomb at: {}".format(pos))

    def check_explosions(self):
        # See if any explosions have ended
        for explosion in self.explosions.copy():
            if explosion.check_over():
                self.explosions = [e for e in self.explosions if explosion.get_pos() != e.get_pos()]
        
        # Determine if any bombs have exploded
        for bomb in self.bombs.copy():
            print("Checking bomb")
            if bomb.check_exploded():
                print("Bomb exploded")
                self.explosions.append(Explosion(bomb.get_pos()))
                self.bombs = [b for b in self.bombs if bomb.get_pos() != b.get_pos()]

        # See if any players overlap with an explosion
        for explosion in self.explosions.copy():
            print("Checking if player in explosion")
            for _, player in self.players.copy().items():
                print("Checking for another player!")
                if explosion.collides_with(player):
                    print("Collision with explosion")
                    player.kill()
                else:
                    print("Player safe!")
            


    def run(self):
        print("Server started. Awaiting input")
        try:
            while True:
                readable, writable, exceptional = (
                        select.select(self.read_list, self.write_list, [])
                        )
                for f in readable:
                    if f is self.listener:
                        msg, addr = f.recvfrom(32)
                        msg = msg.decode()

                        print("{} from {}".format(msg, addr))

                        if len(msg) >= 1:
                            cmd = msg[0]

                        if addr in self.players and self.players[addr].alive == False:
                            continue

                        if cmd == "c":  # New Connection
                            # TODO: Place starting position based off of player count (corners)
                            self.players[addr] = Player((0,0), addr)
                        elif cmd == "u":  # Movement Update
                            if len(msg) >= 2 and addr in self.players:
                                self.handle_movement(msg[1], addr)
                        elif cmd == "b": # Bomb placement
                            self.add_bomb(addr)
                        elif cmd == "d":  # Player Quitting
                            if addr in self.players:
                                del self.players[addr]
                            else:
                                print("Unexpected message from {}: {}".format(addr, msg))
                        
                self.check_explosions()
                for player in self.players:
                    info = []
                    
                    for p in self.players.values():
                        if p.alive:
                            info.append("p{},{}".format(*p.get_pos()))
                        
                    for bomb in self.bombs:
                        info.append("b{},{}".format(*bomb.get_pos()))
                        
                    for explosion in self.explosions:
                        explosion_msg = "e"
                        for rect in explosion.get_rects():
                            print(rect)
                            explosion_msg += "{},{};".format(*rect)
                        
                        print("Expl:{}".format(explosion_msg))
                        explosion_msg = explosion_msg[:-1] # remove trailing semi-colon
                        print("Expl:{}".format(explosion_msg))
                        info.append(explosion_msg)

                    wall_msg = "w"
                    for wall in self.walls:
                        wall_msg += "{},{};".format(*wall.get_pos())
                    wall_msg = wall_msg[:-1] # remove trailing semi-colon
                    info.append(wall_msg) 
                      
                    tosend = '|'.join(info) 
                    tosend += '\n'
                    print(tosend)
                    self.listener.sendto(tosend.encode(), player)
        except KeyboardInterrupt as e:
            print("Game is over.")

if __name__ == "__main__":
    address = os.environ.get("ADDRESS", "0.0.0.0")
    port = os.environ.get("PORT", 3000)
    
    g = GameServer(address, port)
    g.run()
