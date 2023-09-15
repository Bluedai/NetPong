#!/usr/bin/env python3

import socket
import random
import time
import threading
import json
import sys
import pygame
import math

# Konfiguration
server_ip = '85.214.122.18'
# server_ip = '192.168.178.20'
server_port = 12345
Vollbild = False
displaynumber = 1

# globale Variablen initialisieren
pingzeit = ''
latenz = ''
screen = []
running = True
rungame = False

# Farben definieren
schwarz = 0, 0, 0 # Farbe schwarz
blau = 0, 0, 255 # Farbe blau
gelb = 255, 255, 0 # Farbe gelb
weiß = 255, 255, 255 # Farbe weiß
rot = 255, 0, 0 # Farbe rot
grün = 0, 255, 0 # Farbe grün
magenta = 255, 0, 255 # Farbe magenta
cyan = 0, 255, 255 # Farbe cyan
grau = 128, 128, 128 # Farbe grau
regenbogen = [rot, gelb, grün, blau, magenta, cyan] # Farben des Regenbogens

# Farben für das Spiel
farbe_background = schwarz
farbe_spieler = weiß
farbe_ball = blau
farbe_line = gelb
farbe_fps = gelb
farbe_fps_background = farbe_background
farbe_punkte = weiß

# Variablen für die FPS
view_fps = False
clock = pygame.time.Clock()

# Sonstige Variablen
Leinwand = (1920,1080) # 

# Spiel Engine initialisieren
pygame.init()


## Klassen

class Spieler:
    def __init__(self, höhe, breite, farbe, position, tasten):
        self.player_höhe = höhe
        self.player_breite = breite
        self.farbe = farbe
        self.position = position.copy()
        self.tasten = tasten
    def zeichnen(self):
        pygame.draw.rect(screen, self.farbe, (self.position[0], self.position[1], self.player_breite, self.player_höhe))
    def bewegen(self,keys):
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

# Daten vom Server empfangen
def receive_result(client_socket):
    while running:
        try:
            result_data = client_socket.recv(1024)
            if not result_data:
                break
            result = json.loads(result_data.decode())
            process_data(client_socket, result)
        except socket.timeout:
            print("Timeout: receive_result")
            break
        except Exception as e:
            print(f"Fehler beim Empfangen von Daten vom Server: {e}")
            break
    print("receive_result Thread beendet")


# Empfangene Daten vom Server verarbeiten
def process_data(client_socket, received_data):
    if received_data["tag"] == "pong":
        global latenz
        # latenz = round((time.time() - pingzeit) * 1000,2)
        latenz = (time.time() - pingzeit) * 1000
        print(f"Latenz: {latenz:.2f} ms" )
    else:
        print(f"Unbekannte Daten vom Server: {received_data}")


# JSON Daten erstellen
def create_json_data(tag, message):
    json_str = { "tag": tag, "message": message }
    json_data = json.dumps(json_str)
    return json_data


# Daten an Server senden
def send2server(client_socket, tag, message):
    json_data = create_json_data(tag, message)
    try:
        client_socket.send(json_data.encode())
    except socket.timeout:
        print("Timout: send tag: ", tag, " message: ", message)
    except Exception as e:
        print(f"Fehler beim Senden von Daten an den Server: {e}")


# Ping an Server senden
def server_ping(client_socket):
    global pingzeit
    while running:
        time.sleep(5)
        if client_socket.fileno() == -1:
            print("Verbindung zum Server verloren. Ping Thread wird beendet")
            break
        pingzeit = time.time()
        send2server(client_socket, "ping", "ping")


def create_screen():
    global screen
    if Vollbild:
        screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN, display=displaynumber)
    else:
        screen = pygame.display.set_mode(Leinwand, pygame.RESIZABLE, display=displaynumber)
    pygame.display.set_caption("NetPong")
    # pygame.mouse.set_visible(False)

# Hauptprogramm
def main():
    global running
    global rungame
    global screen

    create_screen()

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, server_port))
    client.settimeout(20)  # Timeout von 20 Sekunden
    threads = []

    # Daten Vom Server Thread starten
    result_thread = threading.Thread(target=receive_result, args=(client,))
    threads.append(result_thread)
    result_thread.start()

    # Ping Thread starten
    ping_thread = threading.Thread(target=server_ping, args=(client,))
    threads.append(ping_thread)
    ping_thread.start()

    while running:
        #clear screen
        screen.fill(farbe_background)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                rungame = False
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                # Die Größe des Fensters wird geändert
                print(f"Alte Auflösung: {Leinwand}")
                print(f"Neue Aufösung: {event.w, event.h}")
                # änder_auflösung()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            pygame.event.post(pygame.event.Event(pygame.QUIT)) # Manuell das QUIT Event erzeugen

    # Warten solange noch Threads aktiv sind
    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
