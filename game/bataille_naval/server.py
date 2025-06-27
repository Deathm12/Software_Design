# === FICHIER: server.py ===
import socket
import threading
import pickle

HOST = '127.0.0.1'
PORT = 65432

clients = []
boards = [None, None]
ready = [False, False]
current_turn = 0
winner = None
lock = threading.Lock()


def check_winner():
    for i in [0, 1]:
        if all(cell == 0 for row in boards[i] for cell in row):
            return 1 - i
    return None


def handle_client(conn, addr, player_id):
    global current_turn, winner
    print(f"Client {player_id+1} connecté depuis {addr}")

    conn.send(pickle.dumps({'player_id': player_id}))

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break
            packet = pickle.loads(data)

            with lock:
                if packet['type'] == 'placement':
                    boards[player_id] = packet['board']
                    ready[player_id] = True
                    print(f"Joueur {player_id+1} prêt.")

                    if all(ready):
                        print("Début de la partie")
                        for c in clients:
                            c.send(pickle.dumps({'type': 'start_game'}))

                elif packet['type'] == 'attack' and player_id == current_turn and winner is None:
                    target = packet['target']
                    x, y = target
                    opponent = 1 - player_id
                    hit = False
                    if boards[opponent][y][x] == 1:
                        hit = True
                        boards[opponent][y][x] = 0
                    win = check_winner()
                    if win is not None:
                        winner = win

                    result_packet = {
                        'type': 'attack_result',
                        'player': player_id,
                        'target': target,
                        'hit': hit,
                        'winner': winner
                    }

                    for c in clients:
                        c.send(pickle.dumps(result_packet))

                    if winner is None:
                        current_turn = opponent
                        for c in clients:
                            c.send(pickle.dumps({
                                'type': 'turn_update',
                                'player': current_turn
                            }))

                elif packet['type'] == 'restart':
                    boards[player_id] = None
                    ready[player_id] = False
                    if all(b is None for b in boards):
                        current_turn = 0
                        winner = None
                        print("Réinitialisation du jeu")
        
        except ConnectionResetError:
            break

    print(f"Client {player_id+1} déconnecté.")
    conn.close()


def accept_clients():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()
        print(f"Serveur en écoute sur {HOST}:{PORT}")

        while len(clients) < 2:
            conn, addr = server.accept()
            clients.append(conn)
            threading.Thread(target=handle_client, args=(conn, addr, len(clients)-1), daemon=True).start()

        while True:
            if all(c.fileno() == -1 for c in clients):
                break


if __name__ == '__main__':
    accept_clients()
