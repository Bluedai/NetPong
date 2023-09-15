#!/usr/bin/env python3

# Snippets 
        # debugfont = pygame.font.SysFont("Verdana", 18, bold=False)
        # debugtext = debugfont.render(str(self.farbe)+str(self.typ), True, weiß)
        # screen.blit(debugtext, (100,100))

import sys
import time
import random
import math
import pygame
# import pygame_gui
import socket
import threading
import json

# Spiel Engine initialisieren
pygame.init()

# Konfiguration
Vollbild = False
displaynumber = 1
server_ip = '85.214.122.18'
server_ip = '192.168.178.20'
server_port = 12345

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

# Variablen für die Bewegung
dt = 0 

# Sonstige Variablen
Leinwand = (1920,1080) 
pingzeit = 0
latenz = '' 

# Funktionen

## Netzwerk Funktionen
# Daten Empfangen vom Server
def receive_result(client_socket):
    # client_socket.setblocking(0)
    while running:
        try:
            result_data = client_socket.recv(1024)
            result = json.loads(result_data.decode())
            process_data(client_socket, result)
        except socket.timeout:
            print("Timeout: receive_result")
            break
        except socket.error as e:
            if e.errno == 10035: # Exception für nicht blockierenden Socket
                time.sleep(0.001)
            else:
                print("Socket Fehler: ", e)
        except Exception as e:
            print(f"Fehler beim Empfangen von Daten vom Server: {e}")
    print("receive_result Thread beendet")

# Empfangene Daten vom Server verarbeiten
def process_data(client_socket, received_data):
    if received_data["tag"] == "pong":
        global latenz
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
    pingSekunden = 5
    while running:
        time.sleep(0.5)
        if time.time() - pingzeit > pingSekunden:
            if client_socket.fileno() == -1:
                print("Verbindung zum Server verloren. Ping Thread wird beendet")
                break
            pingzeit = time.time()
            send2server(client_socket, "ping", "ping")

# gestrichelte Linie zeichnen
def gestrichelte_linie_zeichnen(farbe, start, ende, breite, länge, abstand):
    # Berechne die Länge der gesamten Linie
    dx = ende[0] - start[0]
    dy = ende[1] - start[1]
    linienlänge = int( (dx**2 + dy**2)**0.5 )
    angle = math.atan2(dy, dx)
    hilfslänge = linienlänge + abstand
    hilfsende_x = start[0] + hilfslänge * math.cos(angle)
    hilfsende_y = start[1] + hilfslänge * math.sin(angle)
    dx = hilfsende_x - start[0]
    dy = hilfsende_y - start[1]
    linienlänge = int( (dx**2 + dy**2)**0.5 )

    # Berechne die Anzahl der Striche
    anzahl_striche = linienlänge // (länge + abstand)

    # Berechne den Abstand zwischen den Strichen
    dx = dx / anzahl_striche
    dy = dy / anzahl_striche
    dxa = dx / (länge + abstand) * abstand
    dya = dy / (länge + abstand) * abstand

    # Zeichne die Striche
    for i in range(anzahl_striche):
        startx = start[0] + dx * i
        starty = start[1] + dy * i
        endex = start[0] + dx * (i+1) - dxa
        endey = start[1] + dy * (i+1) - dya  
        pygame.draw.line(screen, farbe, (startx, starty), (endex, endey), breite)


# Spielfeld zeichnen
def Spielfeld_zeichnen():
    # Rahmen
    pygame.draw.rect(screen, farbe_line, ( 0,0,screen.get_width(),screen.get_height()), int(randabstand/1.5) )
    # Netz
    netzstart = (screen.get_width() / 2 , 35)
    netzende = (screen.get_width() / 2, screen.get_height())
    if screen.get_height() < 500:
        la = (10,5)
    elif screen.get_height() < 1000:
        la = (20,10)
    else:
        la = (40,20)
    gestrichelte_linie_zeichnen(farbe_line, netzstart, netzende, 3, la[0], la[1])

class Spieler:
    def __init__(self, höhe, breite, farbe, position, tasten):
        self.player_höhe = höhe
        self.player_breite = breite
        self.farbe = farbe
        self.position = position.copy()
        self.tasten = tasten
    def zeichnen(self):
        pygame.draw.rect(screen, self.farbe, (self.position[0], self.position[1], self.player_breite, self.player_höhe))
        # pygame.draw.circle(screen, self.farbe, (int(self.position[0]), int(self.position[1])), 5)
    def bewegen(self,client_socket, keys):
        if keys[self.tasten[0]]:
            self.position.y -= int(300 * dt)
            send2server(client_socket, "move", "UP")
        if keys[self.tasten[1]]:
            self.position.y += int(300 * dt)
            send2server(client_socket, "move", "DOWN")
        if keys[self.tasten[2]]:
            self.position.x -= int(300 * dt)
            send2server(client_socket, "move", "LEFT")
        if keys[self.tasten[3]]:
            self.position.x += int(300 * dt)
            send2server(client_socket, "move", "RIGHT")
    def größe_ändern(self, größe):
        self.player_höhe = größe[0]
        self.player_breite = größe[1]

class Ball:
    def __init__(self, farbe, position):
        self.radius = 10
        self.farbe = farbe
        self.einwurf('random', position)

    def einwurf(self,richtung, position):
        self.geschwindigkeit = 400
        self.position = position.copy()
        choice = random.choice(['oben', 'unten'])
        if richtung == 'links':
            if choice == 'oben':
                self.angle = random.uniform(-math.pi, -(math.pi/5*4))
                print('links oben: ', self.angle)
            else: # links unten 
                self.angle = random.uniform(math.pi, math.pi/5*4)
                print('links unten: ', self.angle)
        elif richtung == 'rechts':
            if choice == 'oben':
                self.angle = random.uniform(-(math.pi/5), 0)
                print('rechts oben: ', self.angle)
            else: # rechts unten
                self.angle = random.uniform(0, math.pi/5)
                print('rechts unten: ', self.angle)
        else:
            self.einwurf(random.choice(['links', 'rechts']), position)

    def zeichnen(self):
        pygame.draw.circle(screen, self.farbe, (int(self.position.x), int(self.position.y)), self.radius)

    def bewegen(self):
        # Berechne die Verschiebung in x- und y-Richtung basierend auf dem Winkel und der Geschwindigkeit
        dx = self.geschwindigkeit * math.cos(self.angle) * dt
        dy = self.geschwindigkeit * math.sin(self.angle) * dt

        # Aktualisiere die Position des Balls
        self.position.x += dx
        self.position.y += dy
        typ = SpielPunkte.get_SpielStatus()

        # Prüfe, ob der Ball rechts das Spielfeld verlässt
        if self.position.x > screen.get_width() - randabstand - self.radius:
            if typ == 'demo':
                self.position.x = screen.get_width() - randabstand - self.radius 
                # Neuen Winkel setzen (Einfallswinkel umkehren)
                self.angle = math.pi - self.angle
            elif typ in ['normal']:
                SpielPunkte.add_Punkt('links')
                SpielPunkte.substract_RestBälle(1)
                self.einwurf('links', pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2) )


        # Prüfe, ob der Ball links das Spielfeld verlässt
        if self.position.x < 0 + randabstand + self.radius:
            if typ == 'demo':
                self.position.x = 0 + randabstand + self.radius 
                # Neuen Winkel setzen (Einfallswinkel umkehren)
                self.angle = math.pi - self.angle
            elif typ in ['normal']:
                SpielPunkte.add_Punkt('rechts')
                SpielPunkte.substract_RestBälle(1)
                self.einwurf('rechts', pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2) )

        # Prüfe, ob der Ball oben das Spielfeld verlässt
        if self.position.y < 0 + randabstand + self.radius:
            self.position.y = 0 + randabstand + self.radius 
            # Neuen Winkel setzen (Einfallswinkel umkehren)
            self.angle = -self.angle

        # Prüfe, ob der Ball unten das Spielfeld verlässt
        if self.position.y > screen.get_height() - randabstand - self.radius:
            self.position.y = screen.get_height() - randabstand - self.radius 
            # Neuen Winkel setzen (Einfallswinkel umkehren)
            self.angle = -self.angle


        # Prüfe, ob der Ball mit einem Spieler kollidiert
        for spieler in Spieler_Liste:
            if spieler.position.x < self.position.x < spieler.position.x + spieler.player_breite:
                if spieler.position.y < self.position.y < spieler.position.y + spieler.player_höhe:
                    if (math.pi/2)*-1 <= math.atan2(math.sin(self.angle), math.cos(self.angle)) <= (math.pi/2)*1:
                        if spieler.position.x > screen.get_width()/2:
                            self.angle = math.pi - self.angle
                    else:
                        if spieler.position.x < screen.get_width()/2: 
                            self.angle = math.pi - self.angle
class Spielumgebung:
    def __init__(self,typ):
        self.typ = typ
        self.set_SpielStatus(typ)

    def set_SpielStatus(self,typ):
        self.typ = typ
        if self.typ in ["init","demo","normal"]:
            self.Spieler_Links = 0
            self.Spieler_Rechts = 0
            self.restBälle = 3
        
        if self.typ == "init":
            self.farbe = grau
        elif self.typ == "demo":
            self.farbe = farbe_punkte
        elif self.typ == "normal":
            self.farbe = farbe_punkte
        elif self.typ == "gameover":
            self.farbe = grau

    def get_SpielStatus(self):
        return self.typ
    
    def add_Punkt(self,spieler):
        if spieler == "links":
            self.Spieler_Links += 1
        elif spieler == "rechts":
            self.Spieler_Rechts += 1

    def substract_RestBälle(self,anzahl):
        global rungame, spieler_links, spieler_rechts
        self.restBälle -= anzahl
        if self.restBälle == 0:
            rungame = False
            spieler_links = None
            spieler_rechts = None
            self.set_SpielStatus("gameover")

    def zeichnen(self):
        font = pygame.font.SysFont("Verdana", 104, bold=False)
        ballfont = pygame.font.SysFont("Verdana", 24, bold=False)
        PunkteLinks  = font.render(str(self.Spieler_Links), True, self.farbe)
        PunkteRechts = font.render(str(self.Spieler_Rechts), True, self.farbe)
        restBälle = ballfont.render(str(self.restBälle), True, self.farbe)
        diff_Links = 110
        diff_Rechts = 47
        screen.blit(PunkteLinks, (screen.get_width()/2-diff_Links, 10))
        screen.blit(PunkteRechts, (screen.get_width()/2+diff_Rechts, 10))
        
        restbälle_width, restbälle_height = restBälle.get_size()
        restbälle_position = (screen.get_width()//2 - restbälle_width//2, (35-randabstand)//2 + randabstand -4 - restbälle_height//2)
        screen.blit(restBälle, restbälle_position)

def änder_auflösung():
    global randabstand,player_höhe,player_breite,player_A_pos,player_B_pos,Leinwand

    randabstand = screen.get_width() * 0.01

    # Variablen für Spieler
    player_höhe = screen.get_height() // 8 
    player_breite = player_höhe // 5
    # Spieler A
    player_A_pos = pygame.Vector2(randabstand , screen.get_height() / 2 - player_höhe / 2)
    # Spieler B
    player_B_pos = pygame.Vector2(screen.get_width() - randabstand - player_breite , screen.get_height() / 2 - player_höhe / 2)

    # Aktuelle Auflösung speichern
    Leinwand = (screen.get_width(), screen.get_height())

        
# FPS auf dem Bildschirm ausgeben
def FPS_zeichnen():
    if view_fps:
        x_position = 30
        y_position = 10
        font = pygame.font.SysFont("Arial", 18)
        # text = font.render("FPS: " + str(round(clock.get_fps())), True, farbe_fps)
        text = font.render("FPS: " + str(round(clock.get_fps())) + "\nLatenz: " + str(round(latenz,1)), True, farbe_fps)
        text_rect = text.get_rect()
        text_rect = text_rect.inflate(3, 0)  # Erweitert das Rechteck um 10 Pixel in alle Richtungen
        text_rect.topleft = (x_position, y_position)  # Ändere die Position des Hintergrundrechtecks
        pygame.draw.rect(screen, farbe_fps_background, text_rect)
        screen.blit(text, (x_position +1 , y_position))  # Zeichne den Text

# Vollbild/Fenster erstellen
if Vollbild:
    # Wenn man (0,0) angibt, dann wird die Bildschirmauflösung des Desktops verwendet
    screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN, display=displaynumber)

else:
    screen = pygame.display.set_mode((800,600),pygame.RESIZABLE, display=displaynumber)
änder_auflösung()
pygame.display.set_caption("Bluedai Pong")

# Hauptschleife des Spiels
running = True
rungame = False

# Socket initialisieren
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((server_ip, server_port))
client.settimeout(20) # Timeout auf 20 Sekunden setzen
threads = []

# Daten Vom Server Thread starten
result_thread = threading.Thread(target=receive_result, args=(client,))
threads.append(result_thread)
result_thread.start()

# Ping Thread starten
ping_thread = threading.Thread(target=server_ping, args=(client,))
threads.append(ping_thread)
ping_thread.start()

SpielPunkte = Spielumgebung('init') # Punkte initialisieren 
while running:
    # Clear screen
    screen.fill(farbe_background)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            sys.exit()
        if event.type == pygame.VIDEORESIZE:
            # Die Auflösung hat sich geändert

            print("Alte Auflösung:", Leinwand)
            print("Neue Auflösung:", event.w, event.h)
            änder_auflösung()


    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_f]:
        view_fps = not view_fps
    if keys[pygame.K_ESCAPE]:
        pygame.event.post(pygame.event.Event(pygame.QUIT))  # Manuell das QUIT-Event erzeugen

    # Spiel starten
    if keys[pygame.K_g]:
        änder_auflösung()
        rungame = True
        Spieler_Liste = []
        Ball_Liste = []
        spieler_links = Spieler(player_höhe, player_breite, farbe_spieler, player_A_pos, (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d))
        Spieler_Liste.append(spieler_links)
        spieler_rechts = Spieler(player_höhe, player_breite, farbe_spieler, player_B_pos, (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT))
        Spieler_Liste.append(spieler_rechts)
        ball = Ball(farbe_ball, pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2) )
        Ball_Liste.append(ball)
        SpielPunkte.set_SpielStatus('normal') # Startet ein Spiel mit 2 Spielern

    if keys[pygame.K_F9]:
        Vollbild = not Vollbild
        if Vollbild:
            screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN, display=displaynumber)
        else:
            screen = pygame.display.set_mode((800,600),pygame.RESIZABLE, display=displaynumber)

    if keys[pygame.K_F12]:
        rungame = True
        Spieler_Liste = []
        Ball_Liste = []
        spieler_links = Spieler(player_höhe, player_breite, farbe_spieler, player_A_pos, (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d) )
        Spieler_Liste.append(spieler_links)
        spieler_rechts = Spieler(player_höhe, player_breite, farbe_spieler, player_B_pos, (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT))
        Spieler_Liste.append(spieler_rechts)
        ball = Ball(farbe_ball, pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2) )
        Ball_Liste.append(ball)
        SpielPunkte.set_SpielStatus('demo') # Startet ein Spiel mit 2 Spielern aber ohne Tore

    # Spiel stoppen
    if keys[pygame.K_h]:
        rungame = False
        spieler_links = None
        spieler_rechts = None
        SpielPunkte.set_SpielStatus('gameover')

    # Spieler + Ball bewegen
    if rungame:
        spieler_links.bewegen(client,keys)
        spieler_rechts.bewegen(client,keys)
        ball.bewegen()

    # Spielfeld zeichnen
    Spielfeld_zeichnen()

    # Punkte + Restbälle zeichnen
    SpielPunkte.zeichnen()

    # Spieler + Ball zeichnen
    if rungame:
        spieler_links.zeichnen()
        spieler_rechts.zeichnen()
        ball.zeichnen()

    FPS_zeichnen()

    dt = clock.tick(60) # max 144 Bilder pro Sekunde
    dt = dt / 1000 
    pygame.display.flip() # Aktualisiere den Bildschirm

pygame.quit()