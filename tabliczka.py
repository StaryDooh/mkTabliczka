import pygame
import math
import random
import sys
import os
import json
import base64

# --- Wersja i Nazwa Gry ---
APP_VERSION = "1.7.0.0"
GAME_TITLE = f"mkTabliczka v{APP_VERSION}"

# --- Ścieżki do zasobów (działa też po spakowaniu PyInstallerem) ---
def resource_path(name):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

# --- System Zapisywania i "Szyfrowania" Rekordów ---
SECRET_KEY = "matematyka_sekret_2026"

APP_FOLDER = "mkTabliczka"
SCORE_FILENAME = "rekordy.dat"

def is_dir_writable(path):
    """Sprawdza, czy w folderze można tworzyć i zapisywać pliki."""
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, f".test_zapisu_{os.getpid()}")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        return True
    except OSError:
        return False

# Rekordy wspólne dla wszystkich użytkowników komputera (%PROGRAMDATA%).
# Gdy folder nie jest zapisywalny, gra korzysta z prywatnego %APPDATA%.
programdata_dir = os.path.join(os.environ.get('PROGRAMDATA') or "", APP_FOLDER)
appdata_dir = os.path.join(os.environ.get('APPDATA') or os.path.expanduser("~"), APP_FOLDER)

if os.environ.get('PROGRAMDATA') and is_dir_writable(programdata_dir):
    game_dir = programdata_dir
else:
    game_dir = appdata_dir
    os.makedirs(game_dir, exist_ok=True)
    print(f"Brak dostępu do wspólnego folderu rekordów - używam: {game_dir}")

SCORE_FILE = os.path.join(game_dir, SCORE_FILENAME)
OLD_SCORE_FILE = os.path.join(appdata_dir, SCORE_FILENAME)  # rekordy z wersji 1.5 i starszych

def xor_cipher(text):
    return "".join(chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(text))

def sort_scores(scores):
    return sorted(scores, key=lambda x: x['score'], reverse=True)[:10]

def read_scores_file(path):
    """Odczytuje rekordy z pliku. Zwraca None, gdy pliku nie ma lub jest uszkodzony."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            b64_bytes = f.read()
        encrypted_str = base64.b64decode(b64_bytes).decode('utf-8')
        data_str = xor_cipher(encrypted_str)
        scores = json.loads(data_str)
        return [s for s in scores if isinstance(s, dict) and 'name' in s and 'score' in s]
    except Exception:
        return None

def save_highscores(scores):
    """Zapisuje rekordy przez plik tymczasowy, aby przerwany zapis nie uszkodził tabeli."""
    data_str = json.dumps(sort_scores(scores))
    encrypted_str = xor_cipher(data_str)
    b64_bytes = base64.b64encode(encrypted_str.encode('utf-8'))
    tmp_file = f"{SCORE_FILE}.{os.getpid()}.tmp"
    try:
        with open(tmp_file, "wb") as f:
            f.write(b64_bytes)
        os.replace(tmp_file, SCORE_FILE)
        return True
    except OSError as e:
        print(f"Nie udało się zapisać rekordów: {e}")
        try:
            os.remove(tmp_file)
        except OSError:
            pass
        return False

def load_highscores():
    scores = read_scores_file(SCORE_FILE)
    if scores is None:
        if os.path.exists(SCORE_FILE):
            print("Błąd odczytu rekordów lub plik uszkodzony. Zaczynamy od zera.")
        return []
    return sort_scores(scores)

def migrate_old_highscores():
    """Przenosi prywatne rekordy użytkownika (wersja 1.5) do wspólnej tabeli."""
    if game_dir == appdata_dir or not os.path.exists(OLD_SCORE_FILE):
        return
    old_scores = read_scores_file(OLD_SCORE_FILE)
    if old_scores:
        merged = load_highscores()
        for record in old_scores:
            if record not in merged:
                merged.append(record)
        if not save_highscores(merged):
            return  # Nie udało się zapisać - spróbujemy przy następnym uruchomieniu
    try:
        os.replace(OLD_SCORE_FILE, OLD_SCORE_FILE + ".przeniesiony")
    except OSError:
        pass

migrate_old_highscores()

# --- Konfiguracja Gry ---
pygame.init()
pygame.mixer.init()

screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption(GAME_TITLE)
clock = pygame.time.Clock()

# Powierzchnie tworzone raz (zamiast w każdej klatce)
overlay_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
overlay_surface.fill((0, 0, 0, 200))
laser_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

# Kolory bazowe
BG_COLOR = (44, 62, 80)
WHITE = (255, 255, 255)
YELLOW = (241, 196, 15)
GREEN = (46, 204, 113)
RED = (231, 76, 60)
BLUE = (52, 152, 219)
GRAY = (149, 165, 166)
DARK_BG = (26, 37, 47)
LASER_COLOR = (255, 0, 0, 120)
BULLET_BOUNCE_SPEED = 12
MAX_BULLET_BOUNCES = 5      # tyle samo odbić, ile pokazuje laser
MIN_AIM_DEG = 12            # najmniejszy kąt lufy nad poziomem (w stopniach)
LASER_MAX_LEVEL = 3         # laser celowniczy widoczny tylko do tego poziomu

# Prędkość spadania kulek (piksele na klatkę): (min, max) dla poziomów 1-4
LEVEL_SPEEDS = {
    1: (0.35, 0.55),
    2: (0.50, 0.75),
    3: (0.65, 0.95),
    4: (0.80, 1.10),
}
LEVEL4_BOOST_PER_POINT = 0.02   # przyspieszenie na poziomie 4 za każdy punkt powyżej 25
LEVEL4_BOOST_MAX = 0.80         # górna granica tego przyspieszenia
MIN_SPEED = 0.30                # najwolniejsze możliwe tempo (po uldze za serie)
RECOIL_TIME = 120           # ms - czas odrzutu lufy po strzale
FLASH_TIME = 80             # ms - czas błysku z lufy

# Wygląd armatki
CANNON_BARREL_LEN = 125
CANNON_DOME_R = 50
CANNON_BASE_W = 340
CANNON_BASE_H = 92
STEEL_DARK = (44, 52, 60)
STEEL = (78, 90, 102)
STEEL_LIGHT = (140, 154, 168)
OUTLINE = (20, 26, 32)
GROUND_COLOR = (34, 49, 63)

# Stany, w których zamiast kursora myszy widać celownik
GAME_STATES = ('PLAYING', 'CHALLENGE_MODE', 'LEVEL_UP', 'MASTER_STREAK', 'SHOW_CORRECTION_MSG')
NAME_MAX_LEN = 10
GAME_OVER_DELAY = 1000      # ms blokady kliknięć na ekranie końcowym

# Słownik kolorów kulek dla poziomów
LEVEL_COLORS = {
    1: {'bg': (52, 152, 219), 'text': (255, 255, 255)},
    2: {'bg': (46, 204, 113), 'text': (26, 37, 47)},
    3: {'bg': (243, 156, 18),  'text': (26, 37, 47)},
    4: {'bg': (155, 89, 182), 'text': (255, 255, 255)}
}

# Wszystkie iloczyny z tabliczki (do losowania sensownych złych odpowiedzi)
TABLE_PRODUCTS = sorted({x * y for x in range(2, 11) for y in range(2, 11)})

# Dźwięki
try:
    sound_shoot = pygame.mixer.Sound(resource_path("strzal.wav"))
    sound_correct = pygame.mixer.Sound(resource_path("dobrze.wav"))
    sound_wrong = pygame.mixer.Sound(resource_path("zle.wav"))
    sound_shoot.set_volume(0.3)
    sound_correct.set_volume(0.6)
    sound_wrong.set_volume(0.6)
except Exception as e:
    print(f"Nie udało się wczytać dźwięków: {e}")
    sound_shoot = sound_correct = sound_wrong = None

# Czcionki
font_giant = pygame.font.SysFont("Arial", 100, bold=True)
font_huge = pygame.font.SysFont("Arial", 60, bold=True)
font_large = pygame.font.SysFont("Arial", 40, bold=True)
font_medium = pygame.font.SysFont("Arial", 28, bold=True)
font_small = pygame.font.SysFont("Arial", 20, bold=True)

class Target:
    def __init__(self, x, y, value, is_correct, speed, radius, bg_color, text_color):
        self.x = x
        self.y = y
        self.value = value
        self.is_correct = is_correct
        self.speed = speed
        self.radius = radius
        self.bg_color = bg_color
        self.text_color = text_color

    def update(self):
        self.y += self.speed

    def draw(self):
        pygame.draw.circle(screen, self.bg_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, self.text_color, (int(self.x), int(self.y)), self.radius, 3)
        text = font_small.render(str(self.value), True, self.text_color)
        text_rect = text.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(text, text_rect)

class Bullet:
    def __init__(self, x, y, angle, radius, speed):
        self.x = x
        self.y = y
        self.angle = angle
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = radius
        self.bounces = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx *= -1
            self.bounces += 1
        elif self.x + self.radius > WIDTH:
            self.x = WIDTH - self.radius
            self.vx *= -1
            self.bounces += 1

        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy *= -1
            self.bounces += 1

    def is_dead(self):
        return self.y > HEIGHT + self.radius or self.bounces > MAX_BULLET_BOUNCES

    def draw(self):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)

def draw_barrel_part(pivot, angle, x0, x1, w0, w1, color):
    """Rysuje fragment lufy (trapez) obrócony o kąt wokół punktu pivot."""
    ca, sa = math.cos(angle), math.sin(angle)
    nx, ny = -sa, ca
    px, py = pivot
    points = [
        (px + ca * x0 + nx * w0 / 2, py + sa * x0 + ny * w0 / 2),
        (px + ca * x1 + nx * w1 / 2, py + sa * x1 + ny * w1 / 2),
        (px + ca * x1 - nx * w1 / 2, py + sa * x1 - ny * w1 / 2),
        (px + ca * x0 - nx * w0 / 2, py + sa * x0 - ny * w0 / 2),
    ]
    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, OUTLINE, points, 2)

def draw_crosshair(pos, color):
    """Celownik w miejscu kursora (z ciemnym obrysem, widoczny na każdym tle)."""
    x, y = pos
    for c, w in ((OUTLINE, 5), (color, 2)):
        pygame.draw.circle(screen, c, (x, y), 16, w)
        pygame.draw.line(screen, c, (x - 24, y), (x - 8, y), w)
        pygame.draw.line(screen, c, (x + 8, y), (x + 24, y), w)
        pygame.draw.line(screen, c, (x, y - 24), (x, y - 8), w)
        pygame.draw.line(screen, c, (x, y + 8), (x, y + 24), w)
    pygame.draw.circle(screen, RED, (x, y), 3)

class Game:
    def __init__(self):
        self.state = 'START'
        self.highscores = load_highscores()
        self.player_name_input = ""
        self.game_over_time = 0
        self.reset_game_vars()

    def reset_game_vars(self):
        self.score = 0
        self.lives = 3
        self.streak = 0
        self.targets = []
        self.bullets = []
        self.frames = 0
        # Środek obrotu lufy - na szczycie podstawy armatki
        self.player_pos = (WIDTH // 2, HEIGHT - CANNON_BASE_H)
        self.last_shot_time = -10000
        self.laser_line_segments = []
        self.current_level = 1
        self.level_up_time = 0
        self.correction_time = 0
        self.streak_time = 0
        self.gained_life_msg = False
        self.speed_relief = 0.0
        self.generate_problem()

    def start_game(self):
        self.reset_game_vars()
        self.state = 'PLAYING'

    def handle_mistake(self):
        """Obsługuje błędny strzał lub ucieczkę prawidłowej kulki."""
        if sound_wrong: sound_wrong.play()
        self.lives -= 1
        self.streak = 0  # Zerujemy mistrzowską serię!
        self.targets.clear()
        self.bullets.clear()

        if self.lives > 0:
            self.state = 'SHOW_CORRECTION_MSG'
            self.correction_time = pygame.time.get_ticks()
        else:
            self.check_highscore()

    def check_highscore(self):
        # Tabela jest wspólna - mogła się zmienić, gdy grał ktoś inny
        self.highscores = load_highscores()
        is_highscore = False
        if len(self.highscores) < 10:
            is_highscore = True
        elif self.score > self.highscores[-1]['score']:
            is_highscore = True

        if is_highscore and self.score > 0:
            self.state = 'INPUT_NAME'
            self.player_name_input = ""
        else:
            self.state = 'GAME_OVER'
            self.game_over_time = pygame.time.get_ticks()

    def save_current_record(self):
        """Zapisuje wynik z wpisanym imieniem (lub 'Anonim')."""
        name = self.player_name_input.strip() or "Anonim"
        self.highscores = load_highscores()  # najświeższa wersja wspólnej tabeli
        self.highscores.append({'name': name, 'score': self.score})
        save_highscores(self.highscores)
        self.highscores = load_highscores()

    def get_level(self):
        if self.score < 5: return 1
        elif self.score < 15: return 2
        elif self.score < 25: return 3
        else: return 4

    def get_max_val(self, level):
        return 30 if level == 1 else (50 if level == 2 else 100)

    def get_speed(self, level):
        low, high = LEVEL_SPEEDS.get(level, LEVEL_SPEEDS[4])
        if level >= 4:
            boost = min(LEVEL4_BOOST_MAX, max(0, (self.score - 25) * LEVEL4_BOOST_PER_POINT))
            low, high = low + boost, high + boost
        base_speed = random.uniform(low, high)
        # Odejmujemy "ulgę" wywalczoną przez poprawne odpowiedzi
        return max(MIN_SPEED, base_speed - self.speed_relief)

    def generate_problem(self):
        level = self.get_level()
        while True:
            self.a = random.randint(2, 10)
            self.b = random.randint(2, 10)
            self.answer = self.a * self.b
            if level == 1 and self.answer <= 30: break
            elif level == 2 and self.answer <= 50: break
            elif level >= 3 and self.answer <= 100: break

    def make_distractor(self, max_val, taken):
        """Losuje złą odpowiedź podobną do typowych pomyłek uczniów."""
        a, b, ans = self.a, self.b, self.answer
        near = {
            a * (b + 1), a * (b - 1), (a + 1) * b, (a - 1) * b,
            a * (b + 2), a * (b - 2), (a + 1) * (b + 1), (a - 1) * (b - 1),
            ans + 1, ans - 1, ans + 10, ans - 10,
        }

        def ok(v):
            return 1 <= v <= max_val and v != ans and v not in taken

        near_pool = [v for v in near if ok(v)]
        table_pool = [v for v in TABLE_PRODUCTS if ok(v)]

        if near_pool and (random.random() < 0.7 or not table_pool):
            return random.choice(near_pool)
        if table_pool:
            return random.choice(table_pool)

        # Awaryjnie: dowolna liczba z zakresu
        value = random.randint(1, max_val)
        while value == ans or value in taken:
            value = random.randint(1, max_val)
        return value

    def spawn_challenge_targets(self):
        """Zrzuca 4 czerwone kulki - tylko jedna jest prawidłowa."""
        self.targets.clear()
        spacing = WIDTH // 5
        level = self.get_level()
        speed = self.get_speed(level)
        max_val = self.get_max_val(level)

        correct_position = random.randint(1, 4)
        current_values = []

        for i in range(1, 5):
            if i == correct_position:
                value = self.answer
                is_correct = True
            else:
                value = self.make_distractor(max_val, current_values)
                is_correct = False

            current_values.append(value)
            # Kulki wyzwania są czerwone (aby zwrócić uwagę gracza na ich charakter)
            self.targets.append(Target(spacing * i, -30, value, is_correct, speed, 35, RED, WHITE))

    def spawn_target(self):
        if self.frames % 80 != 0:
            return
        level = self.get_level()
        x = random.randint(40, WIDTH - 40)
        current_values = [t.value for t in self.targets]
        is_correct = random.random() < 0.35

        if is_correct and self.answer in current_values:
            is_correct = False

        max_val = self.get_max_val(level)
        value = self.answer if is_correct else self.make_distractor(max_val, current_values)
        speed = self.get_speed(level)

        color_theme = LEVEL_COLORS.get(level, LEVEL_COLORS[4])
        self.targets.append(Target(x, -30, value, is_correct, speed, 30, color_theme['bg'], color_theme['text']))

    def aim_angle(self, mouse_pos):
        """Kąt lufy w stronę kursora, ograniczony do górnej półpłaszczyzny.
        Zwraca (kąt, czy_ograniczony)."""
        dx = mouse_pos[0] - self.player_pos[0]
        dy = mouse_pos[1] - self.player_pos[1]
        angle = math.atan2(dy, dx)
        limit = math.radians(MIN_AIM_DEG)
        # Kąty w górę są ujemne: od -pi (w lewo) do 0 (w prawo)
        if -math.pi + limit <= angle <= -limit:
            return angle, False
        if dx >= 0:
            return -limit, True
        return -math.pi + limit, True

    def shoot(self, mouse_pos):
        if sound_shoot: sound_shoot.play()
        angle, _ = self.aim_angle(mouse_pos)
        self.last_shot_time = pygame.time.get_ticks()
        self.bullets.append(Bullet(self.player_pos[0], self.player_pos[1], angle, 6, BULLET_BOUNCE_SPEED))

    def calculate_laser_line(self, mouse_pos):
        self.laser_line_segments = []
        current_angle, _ = self.aim_angle(mouse_pos)
        start_point = self.player_pos
        segments_drawn = 0

        while segments_drawn < MAX_BULLET_BOUNCES:
            p1 = start_point
            projection_length = 3000
            p2 = (p1[0] + math.cos(current_angle) * projection_length,
                  p1[1] + math.sin(current_angle) * projection_length)

            collision_point = p2
            collision_target = None
            wall_hit = None

            for t in self.targets:
                dist = self.get_distance_to_segment((t.x, t.y), p1, p2)
                if dist < t.radius:
                    intersect_dist = self.intersect_circle(p1, math.cos(current_angle), math.sin(current_angle), (t.x, t.y), t.radius)
                    if intersect_dist and intersect_dist < self.get_distance(p1, collision_point):
                        collision_point = (p1[0] + math.cos(current_angle) * intersect_dist,
                                           p1[1] + math.sin(current_angle) * intersect_dist)
                        collision_target = t

            if not collision_target:
                walls = [
                    ((0, 0), (WIDTH, 0), 'top'),
                    ((0, 0), (0, HEIGHT), 'left'),
                    ((WIDTH, 0), (WIDTH, HEIGHT), 'right')
                ]
                for w_p1, w_p2, wall_name in walls:
                    intersection = self.intersect_segments(p1, p2, w_p1, w_p2)
                    if intersection:
                        dist_to_wall = self.get_distance(p1, intersection)
                        if dist_to_wall < self.get_distance(p1, collision_point) and dist_to_wall > 1.0:
                            collision_point = intersection
                            wall_hit = wall_name

            self.laser_line_segments.append((p1, collision_point))

            if collision_target or collision_point[1] > HEIGHT + 10: break

            if wall_hit:
                start_point = collision_point
                segments_drawn += 1
                if wall_hit == 'top': current_angle = -current_angle
                else: current_angle = math.pi - current_angle
            else:
                break

    def get_distance(self, p1, p2): return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    def get_distance_to_segment(self, pt, p1, p2):
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        if dx == 0 and dy == 0: return self.get_distance(pt, p1)
        t = ((pt[0] - p1[0]) * dx + (pt[1] - p1[1]) * dy) / (dx * dx + dy * dy)
        if t < 0: return self.get_distance(pt, p1)
        if t > 1: return self.get_distance(pt, p2)
        return self.get_distance(pt, (p1[0] + t * dx, p1[1] + t * dy))

    def intersect_circle(self, p1, vx, vy, center, radius):
        dx, dy = center[0] - p1[0], center[1] - p1[1]
        a = vx * vx + vy * vy
        b = -2 * (vx * dx + vy * dy)
        c = dx * dx + dy * dy - radius * radius
        discriminant = b * b - 4 * a * c
        if discriminant < 0: return None
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)
        if t1 > 0: return t1
        if t2 > 0: return t2
        return None

    def intersect_segments(self, p1, p2, p3, p4):
        denom = (p1[0] - p2[0]) * (p3[1] - p4[1]) - (p1[1] - p2[1]) * (p3[0] - p4[0])
        if denom == 0: return None
        t = ((p1[0] - p3[0]) * (p3[1] - p4[1]) - (p1[1] - p3[1]) * (p3[0] - p4[0])) / denom
        u = -((p1[0] - p2[0]) * (p1[1] - p3[1]) - (p1[1] - p2[1]) * (p1[0] - p3[0])) / denom
        if 0 <= t <= 1 and 0 <= u <= 1:
            return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
        return None

    def handle_event(self, event, mouse_pos):
        # Tylko lewy, środkowy i prawy przycisk (bez kółka myszy)
        is_click = event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 2, 3)
        is_space = event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE

        if self.state == 'START':
            if is_click or is_space:
                self.start_game()

        elif self.state in ['PLAYING', 'CHALLENGE_MODE']:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.shoot(mouse_pos)

        elif self.state == 'INPUT_NAME':
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.save_current_record()
                    self.state = 'START'
                elif event.key == pygame.K_BACKSPACE:
                    self.player_name_input = self.player_name_input[:-1]
                else:
                    if len(self.player_name_input) < NAME_MAX_LEN and event.unicode.isprintable():
                        self.player_name_input += event.unicode

        elif self.state == 'GAME_OVER':
            if pygame.time.get_ticks() - self.game_over_time < GAME_OVER_DELAY:
                return  # Chronimy przed przeklikaniem ekranu końcowego
            if is_click or is_space:
                self.highscores = load_highscores()
                self.state = 'START'

    def update(self):
        if self.state == 'LEVEL_UP':
            if pygame.time.get_ticks() - self.level_up_time > 2500:
                self.state = 'PLAYING'
            return

        elif self.state == 'MASTER_STREAK':
            if pygame.time.get_ticks() - self.streak_time > 3000:
                self.state = 'PLAYING'
            return

        elif self.state == 'SHOW_CORRECTION_MSG':
            if pygame.time.get_ticks() - self.correction_time > 4000:
                self.state = 'CHALLENGE_MODE'
                self.spawn_challenge_targets()
            return

        elif self.state == 'CHALLENGE_MODE':
            mistake_made = False

            for t in self.targets[:]:
                t.update()
                if t.y > HEIGHT + t.radius:
                    if t.is_correct:
                        mistake_made = True
                    self.targets.remove(t)

            if mistake_made:
                self.handle_mistake()
                return

            for b in self.bullets[:]:
                b.update()
                hit_target = False
                for t in self.targets[:]:
                    dist = math.hypot(b.x - t.x, b.y - t.y)
                    if dist < b.radius + t.radius:
                        hit_target = True
                        if t.is_correct:
                            if sound_correct: sound_correct.play()
                            self.speed_relief += 0.08
                            self.targets.clear()
                            self.bullets.clear()
                            self.state = 'PLAYING'
                            self.generate_problem()
                            return
                        else:
                            mistake_made = True
                        break

                if hit_target or b.is_dead():
                    if b in self.bullets:
                        self.bullets.remove(b)

                if mistake_made:
                    self.handle_mistake()
                    return

            return

        if self.state != 'PLAYING':
            return

        # --- Standardowa Logika GRY (PLAYING) ---
        self.frames += 1
        self.spawn_target()

        for t in self.targets[:]:
            t.update()
            if t.y > HEIGHT + t.radius:
                if t.is_correct:
                    self.handle_mistake()
                    return
                elif t in self.targets:
                    self.targets.remove(t)

        for b in self.bullets[:]:
            b.update()
            hit_target = False
            for t in self.targets[:]:
                dist = math.hypot(b.x - t.x, b.y - t.y)
                if dist < b.radius + t.radius:
                    if t.is_correct:
                        if sound_correct: sound_correct.play()
                        self.score += 1
                        self.streak += 1  # Zwiększamy serię
                        self.targets.clear()
                        self.generate_problem()

                        new_level = self.get_level()
                        if new_level > self.current_level:
                            self.current_level = new_level
                            self.state = 'LEVEL_UP'
                            self.level_up_time = pygame.time.get_ticks()
                            self.bullets.clear()
                            return
                        elif self.streak >= 20:  # Sprawdzamy mistrzowską serię
                            self.state = 'MASTER_STREAK'
                            self.streak_time = pygame.time.get_ticks()
                            self.targets.clear()
                            self.bullets.clear()
                            self.speed_relief += 0.15  # Zwalniamy tempo
                            self.gained_life_msg = False
                            if self.lives < 3:
                                self.lives += 1
                                self.gained_life_msg = True
                            self.streak = 0  # Zerujemy licznik by móc wbić serię od nowa
                            return
                    else:
                        self.handle_mistake()
                        return

                    hit_target = True
                    break

            if hit_target or b.is_dead():
                if b in self.bullets:
                    self.bullets.remove(b)

    def draw(self, mouse_pos):
        screen.fill(BG_COLOR)

        if self.state == 'START':
            title_text = font_huge.render(GAME_TITLE, True, YELLOW)
            screen.blit(title_text, title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 250)))

            hs_title = font_large.render("TOP 10 NAJLEPSZYCH WYNIKÓW", True, WHITE)
            screen.blit(hs_title, hs_title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 150)))

            start_y = HEIGHT // 2 - 80
            if not self.highscores:
                empty_text = font_medium.render("Brak rekordów. Bądź pierwszy!", True, GRAY)
                screen.blit(empty_text, empty_text.get_rect(center=(WIDTH // 2, start_y + 50)))
            else:
                for i, record in enumerate(self.highscores):
                    c = GREEN if i == 0 else WHITE
                    entry_text = font_medium.render(f"{i+1}. {record['name']} - {record['score']} pkt", True, c)
                    screen.blit(entry_text, entry_text.get_rect(center=(WIDTH // 2, start_y + i * 35)))

            start_text = font_medium.render("Kliknij myszką lub naciśnij SPACJĘ, aby rozpocząć grę", True, YELLOW)
            esc_text = font_small.render("ESC - Wyjście z gry", True, GRAY)
            screen.blit(start_text, start_text.get_rect(center=(WIDTH // 2, HEIGHT - 100)))
            screen.blit(esc_text, esc_text.get_rect(center=(WIDTH // 2, HEIGHT - 60)))

        elif self.state == 'LEVEL_UP':
            msg1 = font_huge.render("BRAWO!!!", True, GREEN)
            msg2 = font_large.render(f"PRZECHODZISZ NA POZIOM {self.current_level}", True, WHITE)
            screen.blit(msg1, msg1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
            screen.blit(msg2, msg2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))
            if self.current_level == LASER_MAX_LEVEL + 1:
                msg3 = font_medium.render("Od teraz celujesz bez lasera!", True, YELLOW)
                screen.blit(msg3, msg3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 110)))

        elif self.state == 'MASTER_STREAK':
            msg1 = font_huge.render("MISTRZOWSKA SERIA!!!", True, YELLOW)
            msg2 = font_large.render("Tempo gry spada!", True, WHITE)
            screen.blit(msg1, msg1.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60)))
            screen.blit(msg2, msg2.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

            if self.gained_life_msg:
                msg3 = font_large.render("+1 ŻYCIE", True, GREEN)
                screen.blit(msg3, msg3.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))

        elif self.state == 'SHOW_CORRECTION_MSG':
            screen.blit(overlay_surface, (0, 0))

            msg_top = font_huge.render("ZAPAMIĘTAJ RÓWNANIE!", True, RED)
            msg_eq = font_giant.render(f"{self.a} x {self.b} = {self.answer}", True, YELLOW)

            screen.blit(msg_top, msg_top.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))
            screen.blit(msg_eq, msg_eq.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

        elif self.state in ['PLAYING', 'CHALLENGE_MODE']:
            # Od poziomu 3 gra się bez lasera - trzeba celować samodzielnie
            if self.get_level() <= LASER_MAX_LEVEL:
                self.calculate_laser_line(mouse_pos)
            else:
                self.laser_line_segments = []
            if self.laser_line_segments:
                laser_surface.fill((0, 0, 0, 0))
                for seg in self.laser_line_segments:
                    pygame.draw.line(laser_surface, LASER_COLOR, seg[0], seg[1], 2)
                screen.blit(laser_surface, (0, 0))

            for t in self.targets: t.draw()
            for b in self.bullets: b.draw()

            self.draw_cannon(mouse_pos)

            score_text = font_medium.render(f"Punkty: {self.score}", True, GREEN)
            level_text = font_medium.render(f"Poziom: {self.get_level()}", True, YELLOW)
            lives_text = font_medium.render(f"Życia: {self.lives}", True, RED)
            esc_hint = font_small.render("ESC - Wyjście", True, GRAY)
            streak_text = font_small.render(f"Seria: {self.streak}/20", True, BLUE)

            screen.blit(score_text, (20, 20))
            screen.blit(level_text, (20, 60))
            screen.blit(esc_hint, (20, 100))
            screen.blit(streak_text, (20, 130))
            screen.blit(lives_text, (WIDTH - 120, 20))

            if self.state == 'CHALLENGE_MODE':
                challenge_hint = font_large.render("WYZWANIE: POPRAW BŁĄD!", True, RED)
                screen.blit(challenge_hint, challenge_hint.get_rect(center=(WIDTH // 2, 60)))

        elif self.state == 'INPUT_NAME':
            screen.blit(overlay_surface, (0, 0))

            title_text = font_huge.render("NOWY REKORD TOP 10!", True, GREEN)
            screen.blit(title_text, title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100)))

            score_text = font_large.render(f"Zdobyłeś: {self.score} pkt", True, WHITE)
            screen.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30)))

            prompt_text = font_medium.render("Wpisz swoje imię i naciśnij ENTER:", True, YELLOW)
            screen.blit(prompt_text, prompt_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

            cursor = "|" if (pygame.time.get_ticks() // 500) % 2 == 0 else ""
            input_text_surface = font_large.render(self.player_name_input + cursor, True, WHITE)
            screen.blit(input_text_surface, input_text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))

        elif self.state == 'GAME_OVER':
            screen.blit(overlay_surface, (0, 0))

            go_text = font_huge.render("KONIEC GRY", True, RED)
            screen.blit(go_text, go_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))

            final_score_text = font_large.render(f"Twój wynik: {self.score}", True, WHITE)
            screen.blit(final_score_text, final_score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

            if pygame.time.get_ticks() - self.game_over_time >= GAME_OVER_DELAY:
                restart_text = font_medium.render("Kliknij myszką lub naciśnij SPACJĘ, aby wrócić do menu", True, YELLOW)
                screen.blit(restart_text, restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100)))


        # Celownik zamiast kursora myszy (rysowany na samym wierzchu)
        if self.state in ('PLAYING', 'CHALLENGE_MODE'):
            _, limited = self.aim_angle(mouse_pos)
            draw_crosshair(mouse_pos, GRAY if limited else WHITE)

    def draw_cannon(self, mouse_pos):
        """Rysuje armatkę: lufę, wieżyczkę i podstawę z tablicą działania."""
        cx, cy = self.player_pos
        angle, _ = self.aim_angle(mouse_pos)
        now = pygame.time.get_ticks()
        since_shot = now - self.last_shot_time

        # Ziemia
        pygame.draw.rect(screen, GROUND_COLOR, (0, HEIGHT - 24, WIDTH, 24))
        pygame.draw.line(screen, OUTLINE, (0, HEIGHT - 24), (WIDTH, HEIGHT - 24), 2)

        # Odrzut: lufa cofa się po strzale i płynnie wraca
        recoil = 0
        if since_shot < RECOIL_TIME:
            recoil = 12 * (1 - since_shot / RECOIL_TIME)

        # Lufa (rysowana pod wieżyczką)
        start = 10 - recoil
        end = CANNON_BARREL_LEN - recoil
        draw_barrel_part((cx, cy), angle, start, end, 36, 28, STEEL)                 # rura
        draw_barrel_part((cx, cy), angle, start + 52, start + 62, 40, 40, STEEL_DARK)  # pierścień
        draw_barrel_part((cx, cy), angle, end - 16, end, 36, 36, STEEL_DARK)         # wylot
        # Połysk wzdłuż górnej krawędzi lufy
        nx, ny = -math.sin(angle), math.cos(angle)
        if ny > 0:
            nx, ny = -nx, -ny
        p1 = (cx + math.cos(angle) * (start + 66) + nx * 7, cy + math.sin(angle) * (start + 66) + ny * 7)
        p2 = (cx + math.cos(angle) * (end - 20) + nx * 6, cy + math.sin(angle) * (end - 20) + ny * 6)
        pygame.draw.line(screen, STEEL_LIGHT, p1, p2, 3)

        # Błysk z lufy
        if since_shot < FLASH_TIME:
            k = 1 - since_shot / FLASH_TIME
            mx = cx + math.cos(angle) * (end + 10)
            my = cy + math.sin(angle) * (end + 10)
            pygame.draw.circle(screen, (243, 156, 18), (int(mx), int(my)), int(8 + 14 * k))
            pygame.draw.circle(screen, (255, 236, 150), (int(mx), int(my)), int(4 + 8 * k))

        # Wieżyczka (kopuła)
        pygame.draw.circle(screen, STEEL, (cx, cy), CANNON_DOME_R)
        pygame.draw.circle(screen, OUTLINE, (cx, cy), CANNON_DOME_R, 3)
        pygame.draw.circle(screen, STEEL_LIGHT, (cx - 16, cy - 20), 10)  # odblask
        pygame.draw.circle(screen, STEEL_DARK, (cx, cy), 15)            # oś obrotu
        pygame.draw.circle(screen, OUTLINE, (cx, cy), 15, 2)

        # Podstawa z tablicą działania
        base = pygame.Rect(0, 0, CANNON_BASE_W, CANNON_BASE_H + 20)
        base.midtop = (cx, cy)
        pygame.draw.rect(screen, STEEL_DARK, base, border_top_left_radius=22, border_top_right_radius=22)
        pygame.draw.rect(screen, OUTLINE, base, 3, border_top_left_radius=22, border_top_right_radius=22)
        for rx in (base.left + 16, base.right - 16):  # nity
            for ry in (base.top + 16, base.top + CANNON_BASE_H - 16):
                pygame.draw.circle(screen, STEEL_LIGHT, (rx, ry), 4)
                pygame.draw.circle(screen, OUTLINE, (rx, ry), 4, 1)

        problem_text = font_large.render(f"{self.a} x {self.b} = ?", True, YELLOW)
        plate = pygame.Rect(0, 0, CANNON_BASE_W - 70, CANNON_BASE_H - 22)
        plate.center = (cx, cy + CANNON_BASE_H // 2)
        border_color = RED if self.state == 'CHALLENGE_MODE' else YELLOW
        pygame.draw.rect(screen, DARK_BG, plate, border_radius=12)
        pygame.draw.rect(screen, border_color, plate, 3, border_radius=12)
        screen.blit(problem_text, problem_text.get_rect(center=plate.center))

# --- GŁÓWNA PĘTLA PROGRAMU ---
game = Game()
running = True
cursor_visible = True

while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if game.state == 'INPUT_NAME':
                game.save_current_record()
            running = False
            continue

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Rekord nie przepada przy wyjściu w trakcie wpisywania imienia
            if game.state == 'INPUT_NAME':
                game.save_current_record()
            running = False
            continue

        game.handle_event(event, mouse_pos)

    game.update()

    # Podczas gry kursor myszy jest ukryty - zastępuje go celownik
    want_cursor = game.state not in GAME_STATES
    if want_cursor != cursor_visible:
        pygame.mouse.set_visible(want_cursor)
        cursor_visible = want_cursor

    game.draw(mouse_pos)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
