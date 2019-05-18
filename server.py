import os, socket, select, sys, time
import pygame

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

from util import BLOCKSIZE, X_MAX, Y_MAX

class Bomb(pygame.sprite.Sprite):
    def __init__(self, pos, life=5):
        pygame.sprite.Sprite.__init__(self)
        _, self.rect = load_image("bomb.png")
        self.rect.center = pos
        
        self.life = life
        self.timestamp = time.time()

    def check_exploded(self):
        now = time.time()
        if now - self.timestamp >= self.life:
            return True
        return False

class Explosion():
    def __init__(self, pos, life=1):
        _, self.rect = load_image("explosion.png")
        
        self.rect.center = pos
        self.pos = pos
        self.life = life
        self.timestamp = time.time()

    def check_over(self):
        now = time.time()
        if now - self.timestamp >= self.life:
            return True
        return False

class GameServer():
    def __init__(self, address="127.0.0.1", port=3000):
        self.listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.listener.bind((address, port))
        self.read_list = [self.listener]
        self.write_list = []

        self.stepsize = 20
        self.players = {}
        self.bombs = []
        self.explosions = []

    def handle_movement(self, mv, player):
        pos = self.players[player]

        if mv == "u":
            pos = (pos[0], max(0, pos[1] - self.stepsize))
        elif mv == "d":
            pos = (pos[0], min(Y_MAX, pos[1] + self.stepsize))
        elif mv == "l":
            pos = (max(0, pos[0] - self.stepsize), pos[1])
        elif mv == "r":
            pos = (min(X_MAX, pos[0] + self.stepsize), pos[1])

        self.players[player] = pos

    def add_bomb(self, player):
        # Find the position of the player
        pos = self.players[player]
        self.bombs.append(Bomb(pos))
        print("Placed bomb at: {}".format(pos))

    def check_explosions(self):
        # See if any explosions have ended
        for explosion in self.explosions.copy():
            if explosion.check_over():
                self.explosions = [e for e in self.explosions if explosion.pos != e.pos]
        
        # Determine if any bombs have exploded
        for bomb in self.bombs.copy():
            print("Checking bomb")
            if bomb.check_exploded():
                print("Bomb exploded")
                self.explosions.append(Explosion(bomb.pos))
                self.bombs = [b for b in self.bombs if bomb.pos != b.pos]

                

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

                        if cmd == "c":  # New Connection
                            # TODO: Place starting position based off of player count (corners)
                            self.players[addr] = (0,0)
                        elif cmd == "u":  # Movement Update
                            if len(msg) >= 2 and addr in self.players:
                                self.handle_movement(msg[1], addr)
                        elif cmd == "b": # Bomb placement
                            print("b")
                            self.add_bomb(addr)
                        elif cmd == "d":  # Player Quitting
                            if addr in self.players:
                                del self.players[addr]
                            else:
                                print("Unexpected message from {}: {}".format(addr, msg))
                        
                self.check_explosions()
                for player in self.players:
                    info = []
                    
                    for pos in self.players:
                        info.append("p{},{}".format(*self.players[pos].get_pos()))
                        
                    for bomb in self.bombs:
                        info.append("b{},{}".format(*bomb.get_pos()))

                        
                    for explosion in self.explosions:
                        print(len(self.explosions))
                        info.append("e{},{}".format(*explosion.get_pos()))
                      
                    tosend = '|'.join(info) 
                    tosend += '\n'
                    print(tosend)
                    self.listener.sendto(tosend.encode(), player)
        except KeyboardInterrupt as e:
            print("Game is over.")

if __name__ == "__main__":
    address = os.environ.get("ADDRESS", "127.0.0.1")
    port = os.environ.get("PORT", 3000)
    
    g = GameServer(address, port)
    g.run()
