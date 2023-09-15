#!/usr/bin/env python3

# Imports
import socket
import threading
import time
import json
import sys
import random
import math
import pygame


# Konfiguration
max_clients = 5
server_ip = '85.214.122.18'
server_ip = '192.168.178.20'
server_port = 12345

# dynamische Variablen und feste Vorgaben
active_clients = []                                 # Liste mit allen aktiven Clients
ac_lock = threading.Lock()                          # Lock für die Client-Verwaltung
available_ids = set(range(1, max_clients + 1))      # IDs, die noch vergeben werden können
id_lock = threading.Lock()                          # Lock für die ID-Verwaltung
Move_Puffer = {}                                    # Puffer für die Bewegung
running = True                                      # Server läuft
rungame = False                                     # Spiel läuft
clock = pygame.time.Clock()                         # Spieluhr




# Spiel Engine initialisieren
pygame.init()

# Variablen für die Bewegung
dt = 0 
# Sonstige Variablen
Leinwand = (1920, 1080)

## Klassen
class Spieler:
    def __init__(self, höhe, breite, farbe, position, playerid):
        self.player_höhe = höhe
        self.player_breite = breite
        self.farbe = farbe
        self.position = position.copy()
        self.playerid = playerid
    def zeichnen(self):
        pygame.draw.rect(screen, self.farbe, (self.position[0], self.position[1], self.player_breite, self.player_höhe))
    def bewegen(self, keys):
        if keys[self.tasten[0]]:
            self.position.y -= int(300 * dt)
        if keys[self.tasten[1]]:
            self.position.y += int(300 * dt)
        if keys[self.tasten[2]]:
            self.position.x -= int(300 * dt)
        if keys[self.tasten[3]]:
            self.position.x += int(300 * dt)
    def größe_ändern(self, größe):
        self.player_höhe = größe[0]
        self.player_breite = größe[1]

## Funktionen
# Client ID-Verwaltung
def assign_client_id():
    with id_lock:
        if available_ids:
            client_id = min(available_ids)
            available_ids.remove(client_id)
            return client_id
        return None
def release_client_id(client_id):
    with id_lock: # nicht notwendig bei einem add() auf ein set
        available_ids.add(client_id)

# Socket-Verwaltung
def add_client(client_socket):
    client_id = assign_client_id()
    if client_id is not None:
        active_clients.append((client_id, client_socket))
    else:
        print("Fehler: Keine verfügbare ID mehr!")

def remove_client(client_socket):
    for entry in active_clients:
        if entry[1] == client_socket:
            client_id = entry[0]
            active_clients.remove(entry)
            release_client_id(client_id)
            client_socket.close()
            break

# JSON Daten erstellen
def create_json_data(tag, message):
    json_str = { "tag": tag, "message": message }
    json_data = json.dumps(json_str)
    return json_data


def send2client(client_socket, tag, message):
    json_data = create_json_data(tag, message)
    try:
        client_socket.send(json_data.encode())
    except socket.timeout:
        print("Timout: send tag: ", tag, " message: ", message)

def send2all_clients(tag, message):
    # json_data = create_json_data(tag, message)
    threads = []
    for entry in active_clients:
        client_socket = entry[1]
        thread = threading.Thread(target=send2client, args=(client_socket,tag,message))
        threads.append(thread)
        thread.start()

    # auf alle Threads warten
    for thread in threads:
        thread.join()

# Empfangene Daten vom Client verarbeiten
def process_data(client_socket, received_data):
    # print("debug: eecived_data: ", received_data)
    if received_data["tag"] == "ping":
        send2client(client_socket, "pong", "pong")
    if received_data["tag"] == "move":
        for entry in active_clients:
            if entry[1] == client_socket:
                # print("entry: ", entry)
                Move_Puffer[(entry[0],received_data["message"])] = True
        if received_data["message"] == "LEFT":
            print("move left")
        if received_data["message"] == "RIGHT":
            print("move right")
        if received_data["message"] == "UP":
            print("move up")
        if received_data["message"] == "DOWN":
            print("move down")
    
# Verbindung zum Client
def handle_client(client_socket):
    client_socket.settimeout(20)  # Timeout von 20 Sekunden
    client_number = assign_client_id()
    if client_number is None:
        msg="Keine verfügbaren Plätze mehr! Verbindung wird geschlossen"
        send2client(client_socket, "error", msg)
        print(msg)
        client_socket.close()
        return

    active_clients.append((client_number,client_socket))
    

    # Nachricht an den Client senden, um seine Nummer mitzuteilen
    send2client(client_socket, "client_number", client_number)

    while True:
        try:
            print("Warte auf Nachricht vom Client", client_number)
            # time.sleep(1) # debug
            data = client_socket.recv(1048576)
            decoded_data = data.decode()

            decoder = json.JSONDecoder()
            pos = 0
            while pos < len(decoded_data):
                try:
                    entry, size = decoder.raw_decode(decoded_data[pos:])
                    pos += size
                    # print("Empfangener Eintrag:", entry)
                    process_data(client_socket, entry)
                except json.JSONDecodeError as e:
                    print("Fehler beim Dekodieren des JSON-Eintrags:", e)
                    print("---->>String:", decoded_data)
                    break

            # received_data = json.loads(data.decode())
            # print(f"Empfangene Daten vom Client {client_number}: {received_data} : socket: {client_socket}")
            # process_data(client_socket, received_data)

        except socket.timeout:
            print(f"Timeout: Keine Nachricht vom Client {client_number} erhalten")
            break
        # alle restlichen exceptions abfangen
        except Exception as e:
            print(f"Fehler beim Empfangen von Daten vom Client {client_number}: {e}")
            break
    
    print(f"Verbindung zu Client {client_number} geschlossen:")
    remove_client(client_socket)

def display_active_connections():
    while True:
        print("Aktive Verbindungen:")
        for i, client_socket in enumerate(active_clients, 1):
            print(f"Verbindung {i}: {client_socket}")
        print("move puffer: ", Move_Puffer)
        print("----------------------")
        time.sleep(10)

def socket_init():
    # TCP server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # UDP server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, server_port))
    server.listen(5)
    
    print("Server startet und lauscht auf Port", server_port)
    
    display_thread = threading.Thread(target=display_active_connections)
    display_thread.start()
    
    while True:
        client_socket, addr = server.accept()
        print("Neue Verbindung hergestellt:", addr)
        
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

def Spiel_starten(typ):
    global rungame
    rungame = True
    Spieler_Liste = []
    Ball_Liste = []
    if typ == 'normal':
        spieler_links = Spieler(player_höhe, player_breite, farbe_spieler, player_A_pos, (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d))
        Spieler_Liste.append(spieler_links)
        spieler_rechts = Spieler(player_höhe, player_breite, farbe_spieler, player_B_pos, (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT))
        Spieler_Liste.append(spieler_rechts)
        ball = Ball(farbe_ball, pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2) )
        Ball_Liste.append(ball)
        SpielPunkte.set_SpielStatus('normal') # Startet ein Spiel mit 2 Spielern
    elif typ == 'demo':
        spieler_links = Spieler(player_höhe, player_breite, farbe_spieler, player_A_pos, (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d))
        Spieler_Liste.append(spieler_links)
        spieler_rechts = Spieler(player_höhe, player_breite, farbe_spieler, player_B_pos, (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT))
        Spieler_Liste.append(spieler_rechts)
        ball = Ball(farbe_ball, pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2) )
        Ball_Liste.append(ball)
        SpielPunkte.set_SpielStatus('demo') # Startet ein Spiel mit 2 Spielern aber ohne Tore

def Spiel_stoppen():
    global rungame
    rungame = False
    spieler_links = None
    spieler_rechts = None
    SpielPunkte.set_SpielStatus('gameover')

def move_objects():
    if rungame:
        spieler_links.bewegen()
        spieler_rechts.bewegen()
        ball.bewegen()

def GameServer():
    global rungame
    rungame = False
    # SpielPunkte = Spielumgebung('init') # Punkte initialisieren 
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        # keys = pygame.key.get_pressed()

        # Spieler + Ball bewegen
        move_objects()
 
        # Spielfeld zeichnen
        # Spielfeld_zeichnen()

        # Punkte + Restbälle zeichnen
        # SpielPunkte.zeichnen()

        # Spieler + Ball zeichnen
        # if rungame:
        #     spieler_links.zeichnen()
        #     spieler_rechts.zeichnen()
        #     ball.zeichnen()

        #  FPS_zeichnen()

        dt = clock.tick(60) # max Bilder pro Sekunde
        dt = dt / 1000 
        # pygame.display.flip() # Aktualisiere den Bildschirm

def main():
    main_threads = []
    socket_thread = threading.Thread(target=socket_init)
    main_threads.append(socket_thread)
    socket_thread.start()
    gameserver_thread = threading.Thread(target=GameServer)
    main_threads.append(gameserver_thread)
    gameserver_thread.start()

if __name__ == "__main__":
    main()
