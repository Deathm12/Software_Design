# === FICHIER: client.py ===
import pygame
import socket
import threading
import pickle
import time
import sys
import math

WIDTH, HEIGHT = 1280, 720
GRID_SIZE = 10
CELL_SIZE = 40
GRID_OFFSET = (100, 100)
ADVERSARY_GRID_OFFSET = (600, 100)
SHIP_AREA_OFFSET = (950, 100)

# Couleurs
WHITE = (255, 255, 255)
BLUE = (0, 120, 255)
GRAY = (40, 40, 40)
LIGHT_GRAY = (180, 180, 180)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLACK = (0, 0, 0)

HOST = '127.0.0.1'
PORT = 65432

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 20)
big_font = pygame.font.SysFont("arial", 36)

# Réseau
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((HOST, PORT))

player_id = -1
current_turn = 0
running = True
placing = True
ready = False
my_board = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
attacks = []
incoming_attacks = []
attack_phase = False
winner = None
messages = []
start_time = None

# Eau animée
water_surface = pygame.Surface((WIDTH, HEIGHT))
def draw_water_animation():
    for y in range(0, HEIGHT, 2):
        for x in range(0, WIDTH, 2):
            c = int(80 + 40 * math.sin((x + time.time()*50) * 0.01))
            water_surface.set_at((x, y), (0, 0, c))
    screen.blit(water_surface, (0, 0))

# === Bateau ===
class Ship:
    def __init__(self, length, index):
        self.length = length
        self.index = index
        self.horizontal = True
        self.grid_pos = None
        self.dragging = False
        self.base_pos = (SHIP_AREA_OFFSET[0], SHIP_AREA_OFFSET[1] + index * (CELL_SIZE + 20))
        self.pos = self.base_pos
        self.rect = pygame.Rect(self.pos[0], self.pos[1], length * CELL_SIZE, CELL_SIZE)

    def update_rect(self):
        w = self.length * CELL_SIZE if self.horizontal else CELL_SIZE
        h = CELL_SIZE if self.horizontal else self.length * CELL_SIZE
        self.rect.size = (w, h)
        self.rect.topleft = self.pos

    def draw(self):
        pygame.draw.rect(screen, BLUE, self.rect)  # Remplissage bleu toujours visible
        border_color = (255, 255, 0) if self == selected_ship else BLACK  # Jaune si sélectionné
        pygame.draw.rect(screen, border_color, self.rect, 3)  # Bordure plus visible

ships = [Ship(5, 0), Ship(4, 1), Ship(3, 2), Ship(3, 3), Ship(2, 4)]
selected_ship = None
offset_x = 0
offset_y = 0

def draw_grid(offset, board, show_ships=False, show_hits=False):
    for y in range(GRID_SIZE):
        for x in range(GRID_SIZE):
            rect = pygame.Rect(offset[0] + x * CELL_SIZE, offset[1] + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            color = LIGHT_GRAY
            if show_ships and board[y][x] == 1:
                # Par défaut vert, mais si touché, rouge
                hit = any(move['target'] == (x, y) and move['hit'] for move in incoming_attacks)
                color = RED if hit else GREEN
            pygame.draw.rect(screen, color, rect, 0 if color != LIGHT_GRAY else 1)
    if show_hits:
        if show_ships:
            # Montre les attaques adverses reçues
            for move in incoming_attacks:
                x, y = move['target']
                rect = pygame.Rect(offset[0] + x * CELL_SIZE, offset[1] + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.circle(screen, BLACK, rect.center, 5)  
        else:
            # Montre les attaques qu'on a faites
            for move in attacks:
                x, y = move['target']
                rect = pygame.Rect(offset[0] + x * CELL_SIZE, offset[1] + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.circle(screen, RED if move['hit'] else BLACK, rect.center, 5)

def draw_top_bar():
    pygame.draw.rect(screen, GRAY, (0, 0, WIDTH, 40))
    # Affiche le temps écoulé si la partie a commencé
    if start_time:
        elapsed = int(time.time() - start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        timer_text = font.render(f"{minutes:02}:{seconds:02}", True, WHITE)
        screen.blit(timer_text, (10, 10))

    title_text = font.render("Bataille Navale", True, WHITE)
    screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, 10))

    player_text = font.render(f"Joueur {player_id+1}", True, WHITE)
    screen.blit(player_text, (WIDTH - player_text.get_width() - 10, 10))

def draw_message_panel():
    pygame.draw.rect(screen, GRAY, (ADVERSARY_GRID_OFFSET[0] + GRID_SIZE * CELL_SIZE + 10, 100, 250, 500))
    y = 110
    for msg in messages[-20:]:
        txt = font.render(msg, True, WHITE)
        screen.blit(txt, (ADVERSARY_GRID_OFFSET[0] + GRID_SIZE * CELL_SIZE + 20, y))
        y += 20

def handle_server():
    global attack_phase, winner, placing, start_time, current_turn
    while running:
        try:
            data = sock.recv(4096)
            if not data:
                break
            packet = pickle.loads(data)
            if packet['type'] == 'start_game':
                attack_phase = True
                placing = False
                start_time = time.time()
            elif packet['type'] == 'attack_result':
                if packet['player'] == player_id:
                    attacks.append({
                        'player': packet['player'],
                        'target': packet['target'],
                        'hit': packet['hit']
                    })
                else:
                    incoming_attacks.append({
                        'player': packet['player'],
                        'target': packet['target'],
                        'hit': packet['hit']
                    })
                x, y = packet['target']
                msg = f"Joueur {packet['player']+1}: attaque en {chr(65 + x)}{y+1}, {'Touché !' if packet['hit'] else 'Manqué !'}"
                messages.append(msg)
                if packet['winner'] is not None:
                    winner = packet['winner']
            elif packet['type'] == 'turn_update':
                current_turn = packet['player']
        except:
            break

def apply_ship_positions():
    global my_board
    my_board = [[0]*GRID_SIZE for _ in range(GRID_SIZE)]
    for ship in ships:
        if ship.grid_pos is not None:
            gx, gy = ship.grid_pos
            for i in range(ship.length):
                x = gx + i if ship.horizontal else gx
                y = gy if ship.horizontal else gy + i
                my_board[y][x] = 1

def all_ships_placed():
    return all(ship.grid_pos is not None for ship in ships)

def main():
    global running, placing, ready, player_id, selected_ship, offset_x, offset_y, winner, attack_phase

    data = sock.recv(4096)
    player_id = pickle.loads(data)['player_id']

    threading.Thread(target=handle_server, daemon=True).start()

    while running:
        screen.fill((0, 0, 0))
        draw_water_animation()
        draw_top_bar()

        mx, my = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if placing:
                    for ship in reversed(ships):
                        if ship.rect.collidepoint(event.pos):
                            selected_ship = ship
                            ship.dragging = True
                            offset_x = ship.rect.x - event.pos[0]
                            offset_y = ship.rect.y - event.pos[1]
                            break
                elif attack_phase and winner is None and current_turn == player_id:
                    gx = (mx - ADVERSARY_GRID_OFFSET[0]) // CELL_SIZE
                    gy = (my - ADVERSARY_GRID_OFFSET[1]) // CELL_SIZE
                    if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                        sock.send(pickle.dumps({
                            'type': 'attack',
                            'target': (gx, gy)
                        }))

            elif event.type == pygame.MOUSEBUTTONUP and selected_ship:
                selected_ship.dragging = False
                gx = (selected_ship.rect.x - GRID_OFFSET[0]) // CELL_SIZE
                gy = (selected_ship.rect.y - GRID_OFFSET[1]) // CELL_SIZE
                if 0 <= gx < GRID_SIZE and 0 <= gy < GRID_SIZE:
                    valid = True
                    for i in range(selected_ship.length):
                        x = gx + i if selected_ship.horizontal else gx
                        y = gy if selected_ship.horizontal else gy + i
                        for ship in ships:
                            if ship != selected_ship and ship.grid_pos is not None:
                                sx, sy = ship.grid_pos
                                for j in range(ship.length):
                                    sxj = sx + j if ship.horizontal else sx
                                    syj = sy if ship.horizontal else sy + j
                                    if x == sxj and y == syj:
                                        valid = False
                                        break
                        if not valid:
                            break

                    if valid and (gx + selected_ship.length <= GRID_SIZE if selected_ship.horizontal else gy + selected_ship.length <= GRID_SIZE):
                        selected_ship.grid_pos = (gx, gy)
                        selected_ship.pos = (GRID_OFFSET[0] + gx * CELL_SIZE, GRID_OFFSET[1] + gy * CELL_SIZE)
                    else:
                        selected_ship.grid_pos = None
                        selected_ship.pos = selected_ship.base_pos
                else:
                    selected_ship.grid_pos = None
                    selected_ship.pos = selected_ship.base_pos
                selected_ship.update_rect()
                selected_ship = None

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and selected_ship:
                    selected_ship.horizontal = not selected_ship.horizontal
                    selected_ship.update_rect()

        if placing:
            draw_grid(GRID_OFFSET, my_board, show_ships=True)
            apply_ship_positions()
            for ship in ships:
                if ship.dragging:
                    ship.pos = (mx + offset_x, my + offset_y)
                    ship.update_rect()
                ship.draw()

            rotate_hint = font.render("Astuce: Appuyez sur R pour pivoter un bateau", True, WHITE)
            screen.blit(rotate_hint, (GRID_OFFSET[0], SHIP_AREA_OFFSET[1] - 30))

            if all_ships_placed():
                validate_text = big_font.render("Appuyez sur ENTRÉE pour valider", True, WHITE)
                screen.blit(validate_text, (WIDTH//2 - validate_text.get_width()//2, HEIGHT - 60))

                keys = pygame.key.get_pressed()
                if keys[pygame.K_RETURN] and not ready:
                    sock.send(pickle.dumps({'type': 'placement', 'board': my_board}))
                    ready = True

        elif attack_phase:
            draw_grid(GRID_OFFSET, my_board, show_ships=True, show_hits=True)
            draw_grid(ADVERSARY_GRID_OFFSET, [[0]*GRID_SIZE for _ in range(GRID_SIZE)], show_hits=True)
            draw_message_panel()
            turn_text = font.render("À vous de jouer" if player_id == (len(attacks) % 2) else "Tour de l'adversaire", True, WHITE)
            screen.blit(turn_text, (GRID_OFFSET[0], GRID_OFFSET[1] + GRID_SIZE * CELL_SIZE + 10))

        if winner is not None:
            text = "VOUS AVEZ GAGNÉ !" if winner == player_id else "VOUS AVEZ PERDU..."
            color = GREEN if winner == player_id else RED
            result = big_font.render(text, True, color)
            screen.blit(result, (WIDTH//2 - result.get_width()//2, HEIGHT//2 - 30))

            restart_text = font.render("R pour rejouer | Q pour quitter", True, WHITE)
            screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 20))

            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                sock.send(pickle.dumps({'type': 'restart'}))
                placing = True
                ready = False
                attack_phase = False
                winner = None
                attacks.clear()
                messages.clear()
                start_time = None
                for ship in ships:
                    ship.grid_pos = None
                    ship.pos = ship.base_pos
                    ship.horizontal = True
                    ship.update_rect()

            elif keys[pygame.K_q]:
                running = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sock.close()
    sys.exit()


if __name__ == '__main__':
    main()
