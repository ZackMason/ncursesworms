import curses
from sys import platform
import math, random, socket, argparse, time
import numpy as np

from help import get_line

# the code is very messy 
# I was mostly focused on 
# getting it done quickly
# rather than style :)

#map[y][x]
def generate_map(sy, sx):
    map = [[' ' for j in range(sx)] for i in range(sy)]

    for j, row in enumerate(map):
        for i, cell in enumerate(row):
            if random.random() < 0.13 + 0.6*j/sy + math.sin(i/sx)*0.13:
                row[i] = '#'

    for i in range(220):
        map = automata(map)

    return map

def automata(map, wall = '#'):
    new_map = map[:]

    for i, row in enumerate(map[1:-1],1):
        for j, cell in enumerate(row[1:-1],1):
            count = 0

            for lx in [-1, 0, 1]:
                for ly in [-1, 0, 1]:
                    if lx != 0 and ly != 0 and map[i+ly][j+lx] == wall:
                        count += 1

            if count >= 4:
                new_map[i][j] = wall
            elif count <= 1:
                new_map[i][j] = ' '

    return new_map

def get_floor(map, player):
    try:
        return map[player[1]+1][player[0]]
    except:
        return ' '

def move_player(player, amount, map, wall = ['#']):
    try_x = player[0] + amount

    if map[player[1]][try_x] in wall:
        for offset in [-1, 1]:
            try_y = player[1] + offset
            if map[try_y][try_x] not in wall:
                player[0] = try_x
                player[1] = try_y
                return True
    else:
        player[0] = try_x
        return True
    return False

def draw_line(stdscr, start, len, angle, char = '.', map=None, color=0):
    ax = math.cos(math.radians(angle)) * len + start[0]
    ay = math.sin(math.radians(angle)) * len + start[1]

    line = get_line(start[:2], [int(ax),int(ay)])

    for point in line:
        if map and map[point[1]][point[0]] == '#': return line
        if point[0] == start[0] and point[1] == start[1]: continue
        try:
            stdscr.addch(point[1], point[0], char, curses.color_pair(color))
        except:
            pass
    return line


def print_game(stdscr, map, players):
    p1 = players[0]
    p2 = players[1]

    for i, row in enumerate(map):
        try:
            stdscr.addstr(i, 0, ''.join(row), curses.color_pair(3))
        except curses.error:
            pass

    try:
        stdscr.addch(p1[1], p1[0], '@')
        stdscr.addch(p2[1], p2[0], '@')

        stdscr.addstr(p1[1]-2,p1[0]-p1[3]//2, '\u2192'*p1[3], curses.color_pair(4))
        stdscr.addstr(p2[1]-2,p2[0]-p2[3]//2, '\u2192'*p2[3], curses.color_pair(4))

        stdscr.addstr(p1[1]-1,p1[0]-p1[2]//2, '\u2665'*p1[2], curses.color_pair(1))
        stdscr.addstr(p2[1]-1,p2[0]-p2[2]//2, '\u2665'*p2[2], curses.color_pair(2))
    except:
        pass

def main(stdscr):
    parser = argparse.ArgumentParser(description='A program demonstrating the use of sockets')
    parser.add_argument('-p', '--port', type=int, nargs='?', default=8080)
    parser.add_argument('-s', '--server',  dest='server', action='store_true')
    parser.add_argument('-c', '--client',  dest='server', action='store_false')
    parser.add_argument('-o', '--offline', action='store_true')
    args = parser.parse_args()
    port = args.port
    host = '127.0.0.1'
    is_server = args.server
    is_offline = args.offline

    curses.init_color(curses.COLOR_YELLOW, 1000, 1000, 0)
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)

    if is_offline:
        game_loop(stdscr, True, None, is_offline)
    else:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if is_server or is_offline:
                s.bind((host, port))

                stdscr.clear()
                stdscr.addstr(0,0, 'Waiting for connection')
                stdscr.refresh()
                s.listen(1)

                conn, addr = s.accept()
                with conn:

                    seed = random.randint(0,13371337)
                    conn.send(str(seed).encode())
                    random.seed(seed)

                    game_loop(stdscr, is_server, conn, is_offline)

            else:
                s.connect((host, port))
                game_loop(stdscr,is_server, s, is_offline)

def do_gravity(stdscr, map, players, sleep=True):
    falling = False
    for p in players:
        if get_floor(map, p) == ' ':
            p[1] += 1
            falling = True
    if sleep and falling: time.sleep(0.1)
    return players, falling

def shoot(stdscr, player, angle, map, enemy_player):
    player[3] = 0
    ax = math.cos(math.radians(angle)) * 100 + player[0]
    ay = math.sin(math.radians(angle)) * 100 + player[1]

    line = draw_line(stdscr, player, 100, angle, '*', map, 2)
    stdscr.refresh()
    time.sleep(0.3)

    explosion_delay = .1
    explosion_count = 3

    for point in line:
        try:
            if map[point[1]][point[0]] == '#':
                for i in range(explosion_count):
                    do_explosion(stdscr, point, 3, map, enemy_player)
                    time.sleep(explosion_delay)
                return
        except:
            return

def do_explosion(stdscr, position, radius, map, enemy_player, char = '*#$!(%&@#!@%?@#!^?^@??;:+=-<>~&)'):
    for i in range(-radius,radius):
        for j in range(-radius,radius):
            dist = math.sqrt(i*i + j*j)
            if dist <= radius:
                colors = [1, 2]

                if enemy_player[:2] == [position[0] + i, position[1] + j]:
                    enemy_player[2] -= 1
                try:
                    map[position[1] + j][ position[0] + i] = ' '
                    stdscr.addch(position[1] + j, position[0] + i, random.choice(char), curses.color_pair(random.choice(colors)))
                except:
                    pass
    stdscr.refresh()

def game_loop(stdscr, is_server, conn, is_offline):
    sy, sx = stdscr.getmaxyx()

    if not is_server:
        random.seed(int(conn.recv(1024).decode()))

    map = generate_map(sy, sx)

    starting_health = 10
    number_of_moves = 5

    p1 = [ 15, 3, starting_health, number_of_moves]
    p2 = [ sx - 15, 3, starting_health, number_of_moves]

    players = [p1,p2]
    turn_index = 0

    while True:
        took_turn = False
        cur_player = players[turn_index]
        stdscr.clear()

        falling = True
        while falling:
            if check_game_over(stdscr, players, sy-1): return
            players, falling = do_gravity(stdscr, map, players)

            stdscr.clear()
            print_game(stdscr, map, players)
            stdscr.refresh()


        key = ''

        # attempt to fix input bug when its not your turn
        # will not work for the first char
        try:
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        except ImportError:
            import sys, termios    #for linux/unix
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)

        if is_offline:
            key = stdscr.getkey()
        elif is_server:
            if turn_index == 0: # get input from player and send
                key = stdscr.getkey()
                if key != 'f':
                    conn.send(str.encode(key))
            else: # listen for opponent
                key = conn.recv(16).decode()
                if key[0] == 'f':
                    angle = int(key[2:])
                    shoot(stdscr, players[1], angle, map, players[(turn_index+1)%2])
        else:
            if turn_index == 0: # listen for opponent
                key = conn.recv(16).decode()
                if key[0] == 'f':
                    angle = int(key[2:])
                    shoot(stdscr, players[0], angle, map, players[(turn_index+1)%2])
            else: # get input from player and send
                key = stdscr.getkey()
                if key != 'f':
                    conn.send(str.encode(key))

        if key == 'q': break

        if key == 'a':
            took_turn = move_player(players[turn_index], -1, map)
        if key == 'd':
            took_turn = move_player(players[turn_index], 1, map)

        if key == 'k':
            cur_player[2] = 0


        shot = False
        if key == 'f':
            shooting_player = players[turn_index]
            players, shot = fire_mode(stdscr, map, players, shooting_player, conn, turn_index)
            if not shot:
                #turn_index = (turn_index + 1) % 2
                pass
            else:
                took_turn = True

        if took_turn:
            cur_player[3] -= 1
        if cur_player[3] <= 0:
            cur_player[3] = number_of_moves
            turn_index = (turn_index + 1) % 2

def fire_mode(stdscr, map, players, shooting_player, conn, turn_index):
    angle = -90
    actually_shot = False
    while shooting_player: # fire mode
        stdscr.clear()

        print_game(stdscr, map, players)

        # draw line
        draw_line(stdscr, shooting_player, 30, angle)

        stdscr.refresh()
        key = stdscr.getkey()

        if key == 'w' or key == 'a':
            angle -= 2
        elif key == 's' or key == 'd':
            angle += 2
        elif key == 'f':
            shooting_player = None
        elif key == ' ':
            conn.send(f'f {angle}'.encode())
            actually_shot = True
            shoot(stdscr, shooting_player, angle, map, players[(turn_index+1)%2])
            shooting_player[3] = 0
            shooting_player = None

    return players, actually_shot

def check_game_over(stdscr, players, kill_y):
    for i, player in enumerate(players):
        if player[2] <= 0 or player[1] >= kill_y:
            stdscr.clear()
            stdscr.addstr(0, 0, f'Player {i} has lost')
            stdscr.addstr(1, 0, f'Press q to exit')
            stdscr.refresh()
            key = ''
            while key != 'q':
                key = stdscr.getkey()
            return True
    return False

if __name__ == '__main__':
    curses.wrapper(main)