"""
2 Player Tag Game - Power Cubes Edition

HOW TO PLAY:
- One player is the Chaser and tries to tag the Runner.
- Tag the other player to swap roles and score a point.
- Most tags in 60 seconds wins.
- Tie = Sudden Death overtime.

POWER CUBES:
SPEED  - Move 2x faster for 5 seconds
SHIELD - Cannot be tagged for 4 seconds
GHOST  - Walk through obstacles for 4 seconds
SWAP   - Instantly swap who is the chaser

CONTROLS:
Player 1 (Blue)  - W A S D
Player 2 (Red)   - Arrow Keys
"""

import pygame
import sys
import random

# ── Initialise pygame ─────────────────────────────────────
pygame.init()

# ── Window settings ───────────────────────────────────────
SCREEN_WIDTH  =1000
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("2-Player Tag Game - Power Cubes!")

clock = pygame.time.Clock()
FPS   = 60

# ── Colours ───────────────────────────────────────────────
WHITE       = (255, 255, 255)
BLACK       = (  0,   0,   0)
BLUE        = ( 50, 120, 220)
BLUE_DARK   = ( 20,  60, 140)
BLUE_LIGHT  = (100, 160, 255)
RED         = (220,  50,  50)
RED_DARK    = (140,  20,  20)
RED_LIGHT   = (255, 100, 100)
GREEN       = ( 50, 200,  80)
YELLOW      = (255, 220,   0)
ORANGE      = (255, 140,   0)
CYAN        = (  0, 210, 210)
PINK        = (255,  80, 180)
GRAY        = (180, 180, 180)
DARK_GRAY   = ( 80,  80,  90)
BG_COLOR    = ( 30,  30,  40)
HUD_COLOR   = ( 18,  18,  28)

OBSTACLE_COLORS = [
    ( 80,  60, 100), ( 60,  90,  80), (100,  70,  50), ( 50,  80, 110),
    ( 90,  60,  60), ( 60, 100,  60), ( 90,  80,  50), ( 70,  70,  90),
]

# ── Fonts ─────────────────────────────────────────────────
font_big    = pygame.font.SysFont("Arial", 48, bold=True)
font_medium = pygame.font.SysFont("Arial", 26)
font_small  = pygame.font.SysFont("Arial", 19)
font_tiny   = pygame.font.SysFont("Arial", 14)

# ── Game constants ────────────────────────────────────────
PLAYER_SIZE         = 40
PLAYER_SPEED        = 4
GAME_DURATION       = 60
SUDDEN_DEATH_TIME   = 30
TAG_COOLDOWN_FRAMES = 90
CUBE_SIZE           = 22        # power cube square size
CUBE_SPAWN_INTERVAL = 8         # seconds between new cube spawns
POWERUP_DURATION    = 60 * 4   # 4 seconds in frames (speed = 5s)

# ── Arena ─────────────────────────────────────────────────
ARENA_TOP  = 65
ARENA_RECT = pygame.Rect(0, ARENA_TOP, SCREEN_WIDTH, SCREEN_HEIGHT - ARENA_TOP)

# ── Power-up types ────────────────────────────────────────
# Each type has: name, colour, description shown in HUD
POWERUP_TYPES = {
    "speed":  {"color": YELLOW, "label": "SPEED",  "desc": "2x Speed!",          "duration": 60 * 5},
    "shield": {"color": CYAN,   "label": "SHIELD", "desc": "Tag Shield!",         "duration": 60 * 4},
    "ghost":  {"color": PINK,   "label": "GHOST",  "desc": "Ghost Mode!",         "duration": 60 * 4},
    "swap":   {"color": ORANGE, "label": "SWAP",   "desc": "Roles Swapped!",      "duration": 0},
}


# ══════════════════════════════════════════════════════════
#  OBSTACLE CLASS
# ══════════════════════════════════════════════════════════
class Obstacle:
    def __init__(self, x, y, w, h, color):
        self.rect         = pygame.Rect(x, y, w, h)
        self.color        = color
        self.border_color = tuple(max(0, c - 40) for c in color)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color,        self.rect, border_radius=4)
        pygame.draw.rect(surface, self.border_color, self.rect, width=2, border_radius=4)
        highlight = pygame.Rect(self.rect.x + 3, self.rect.y + 3, self.rect.width - 6, 4)
        lighter = tuple(min(255, c + 40) for c in self.color)
        pygame.draw.rect(surface, lighter, highlight, border_radius=2)


def create_obstacles():
    data = [
        (150, 150,  20, 120, 0),
        (300, 100, 120,  20, 1),
        (500, 150,  20, 120, 2),
        (200, 320, 120,  20, 3),
        (480, 320, 120,  20, 4),
        (340, 220,  20, 100, 5),
        (130, 430, 160,  20, 6),
        (510, 430, 160,  20, 7),
    ]
    return [Obstacle(x, y, w, h, OBSTACLE_COLORS[ci]) for x, y, w, h, ci in data]


# ══════════════════════════════════════════════════════════
#  POWER CUBE CLASS
# ══════════════════════════════════════════════════════════
class PowerCube:
    """
    A glowing cube that players walk over to collect.
    Bobs up and down slightly for visibility.
    """

    def __init__(self, x, y, kind):
        self.kind    = kind                          # "speed", "shield", "ghost", "swap"
        self.color   = POWERUP_TYPES[kind]["color"]
        self.label   = POWERUP_TYPES[kind]["label"]
        self.rect    = pygame.Rect(x, y, CUBE_SIZE, CUBE_SIZE)
        self.alive   = True
        self.bob_tick = random.randint(0, 60)        # offset so cubes don't all bob together

    def update(self):
        self.bob_tick += 1

    def draw(self, surface):
        if not self.alive:
            return

        # Bob offset: ±3 pixels using a sine-like pattern
        bob = int(3 * abs((self.bob_tick % 60) / 30 - 1) - 1.5)
        draw_rect = self.rect.move(0, bob)

        # Outer glow ring
        glow = draw_rect.inflate(8, 8)
        glow_surf = pygame.Surface((glow.width, glow.height), pygame.SRCALPHA)
        r, g, b = self.color
        pygame.draw.rect(glow_surf, (r, g, b, 60), glow_surf.get_rect(), border_radius=6)
        surface.blit(glow_surf, glow.topleft)

        # Main cube body
        pygame.draw.rect(surface, self.color,  draw_rect, border_radius=4)
        dark = tuple(max(0, c - 60) for c in self.color)
        pygame.draw.rect(surface, dark, draw_rect, width=2, border_radius=4)

        # Small icon letter inside the cube
        icon = font_tiny.render(self.label[0], True, BLACK)
        ix = draw_rect.centerx - icon.get_width() // 2
        iy = draw_rect.centery - icon.get_height() // 2
        surface.blit(icon, (ix, iy))


def spawn_power_cube(obstacles, existing_cubes):
    """
    Pick a random open spot in the arena that doesn't overlap
    any obstacle or existing cube, then create a random power cube.
    """
    kinds = list(POWERUP_TYPES.keys())
    margin = 20
    for _ in range(100):   # try up to 100 times to find a free spot
        x = random.randint(margin, SCREEN_WIDTH  - CUBE_SIZE - margin)
        y = random.randint(ARENA_TOP + margin, SCREEN_HEIGHT - CUBE_SIZE - margin)
        candidate = pygame.Rect(x, y, CUBE_SIZE, CUBE_SIZE)

        # Check no overlap with obstacles
        blocked = any(candidate.colliderect(o.rect) for o in obstacles)
        # Check no overlap with existing cubes
        blocked = blocked or any(candidate.colliderect(c.rect) for c in existing_cubes if c.alive)

        if not blocked:
            return PowerCube(x, y, random.choice(kinds))

    return None   # couldn't find a spot (very rare)


# ══════════════════════════════════════════════════════════
#  PLAYER CLASS
# ══════════════════════════════════════════════════════════
class Player:
    def __init__(self, x, y, color, color_dark, color_light, name, controls):
        self.start_x    = x
        self.start_y    = y
        self.rect       = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.color      = color
        self.color_dark = color_dark
        self.color_light= color_light
        self.name       = name
        self.controls   = controls
        self.score      = 0
        self.is_chaser  = False

        # Active power-up state
        self.powerup        = None   # current power-up kind string or None
        self.powerup_timer  = 0      # frames remaining
        self.powerup_flash  = 0      # frames for collection flash effect

    # ── Properties derived from active power-up ───────────
    @property
    def speed(self):
        return PLAYER_SPEED * 2 if self.powerup == "speed" else PLAYER_SPEED

    @property
    def is_shielded(self):
        return self.powerup == "shield"

    @property
    def is_ghost(self):
        return self.powerup == "ghost"

    def apply_powerup(self, kind):
        """Activate a collected power-up."""
        info = POWERUP_TYPES[kind]
        self.powerup       = kind
        self.powerup_timer = info["duration"]
        self.powerup_flash = 40   # short flash on collection

    def update_powerup(self):
        """Tick down the power-up timer each frame."""
        if self.powerup_flash > 0:
            self.powerup_flash -= 1
        if self.powerup and self.powerup_timer > 0:
            self.powerup_timer -= 1
            if self.powerup_timer <= 0:
                self.powerup = None

    def move(self, keys, obstacles):
        dx = (-self.speed if keys[self.controls['left']]  else 0 ) + \
             ( self.speed if keys[self.controls['right']] else 0 )
        dy = (-self.speed if keys[self.controls['up']]    else 0 ) + \
             ( self.speed if keys[self.controls['down']]  else 0 )

        self.rect.x += dx
        if not self.is_ghost:
            for obs in obstacles:
                if self.rect.colliderect(obs.rect):
                    if dx > 0: self.rect.right = obs.rect.left
                    elif dx < 0: self.rect.left = obs.rect.right

        self.rect.y += dy
        if not self.is_ghost:
            for obs in obstacles:
                if self.rect.colliderect(obs.rect):
                    if dy > 0: self.rect.bottom = obs.rect.top
                    elif dy < 0: self.rect.top = obs.rect.bottom

        self.rect.clamp_ip(ARENA_RECT)

    def draw(self, surface):
        # Power-up collection flash (white outline)
        if self.powerup_flash > 0:
            flash_rect = self.rect.inflate(12, 12)
            pygame.draw.rect(surface, WHITE, flash_rect, width=3, border_radius=10)

        # Shield ring (cyan)
        if self.is_shielded:
            shield_rect = self.rect.inflate(10, 10)
            pygame.draw.rect(surface, CYAN, shield_rect, width=3, border_radius=9)

        # Ghost mode: draw with lower opacity using a surface
        if self.is_ghost:
            ghost_surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
            r, g, b = self.color
            pygame.draw.rect(ghost_surf, (r, g, b, 130),
                             ghost_surf.get_rect(), border_radius=6)
            surface.blit(ghost_surf, self.rect.topleft)
        else:
            pygame.draw.rect(surface, self.color,      self.rect, border_radius=6)
            pygame.draw.rect(surface, self.color_dark, self.rect, width=3, border_radius=6)

        # Speed trail dots
        if self.powerup == "speed":
            for i in range(1, 4):
                alpha = 80 - i * 20
                tx = self.rect.centerx - (10 * i if self.rect.x > 100 else -10 * i)
                ty = self.rect.centery
                trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                r, g, b = YELLOW
                pygame.draw.circle(trail_surf, (r, g, b, alpha), (4, 4), 4)
                surface.blit(trail_surf, (tx - 4, ty - 4))

        # Shine dot
        pygame.draw.circle(surface, self.color_light,
                           (self.rect.x + 10, self.rect.y + 10), 4)

        # "IT!" label for chaser
        if self.is_chaser:
            glow = self.rect.inflate(8, 8)
            pygame.draw.rect(surface, YELLOW, glow, width=2, border_radius=8)
            label = font_small.render("IT!", True, YELLOW)
            surface.blit(label, (self.rect.centerx - label.get_width() // 2,
                                 self.rect.top - 26))

        # Active power-up icon below the player
        if self.powerup:
            info  = POWERUP_TYPES[self.powerup]
            badge = font_tiny.render(info["label"], True, info["color"])
            surface.blit(badge, (self.rect.centerx - badge.get_width() // 2,
                                 self.rect.bottom + 4))


# ══════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════
def draw_centered_text(surface, text, font, color, y):
    rendered = font.render(text, True, color)
    surface.blit(rendered, ((SCREEN_WIDTH - rendered.get_width()) // 2, y))


def draw_timer_bar(surface, seconds_left, total_seconds, sudden_death):
    bar_w, bar_h = 260, 8
    bx = (SCREEN_WIDTH - bar_w) // 2
    by = 56
    ratio = max(0, seconds_left / total_seconds)

    if sudden_death:
        color = RED if (int(seconds_left) % 2 == 0) else ORANGE
    elif ratio > 0.5: color = GREEN
    elif ratio > 0.25: color = ORANGE
    else: color = RED

    pygame.draw.rect(surface, DARK_GRAY, (bx, by, bar_w, bar_h), border_radius=4)
    filled = int(bar_w * ratio)
    if filled > 0:
        pygame.draw.rect(surface, color, (bx, by, filled, bar_h), border_radius=4)


def draw_powerup_legend(surface):
    """Small legend in the bottom-right corner showing all power-up types."""
    items = [
        (YELLOW, "Speed  2x fast"),
        (CYAN,   "Shield no tags"),
        (PINK,   "Ghost  thru walls"),
        (ORANGE, "Swap   swap roles"),
    ]
    x = SCREEN_WIDTH - 160
    y = SCREEN_HEIGHT - 10 - len(items) * 18
    for color, text in items:
        pygame.draw.rect(surface, color, (x, y + 3, 10, 10), border_radius=2)
        lbl = font_tiny.render(text, True, GRAY)
        surface.blit(lbl, (x + 16, y))
        y += 18


# ══════════════════════════════════════════════════════════
#  SCREEN: START
# ══════════════════════════════════════════════════════════
def show_start_screen():
    while True:
        screen.fill(BG_COLOR)
        draw_centered_text(screen, "2-Player Tag Game", font_big, YELLOW, 40)
        draw_centered_text(screen, "Power Cubes Edition!", font_small, ORANGE, 100)

        lines = [
            "Tag the other player to score — most tags in 60s wins!",
            "Tie = Sudden Death (first tag wins)!",
            "",
            "Pick up glowing cubes for power-ups:",
        ]
        for i, line in enumerate(lines):
            draw_centered_text(screen, line, font_tiny, WHITE, 145 + i * 22)

        # Power-up colour swatches
        cube_info = [
            (YELLOW, "SPEED  — 2x faster for 5s"),
            (CYAN,   "SHIELD — can't be tagged for 4s"),
            (PINK,   "GHOST  — walk through walls for 4s"),
            (ORANGE, "SWAP   — instantly swap chaser roles!"),
        ]
        for i, (col, desc) in enumerate(cube_info):
            sx = 220
            sy = 240 + i * 28
            pygame.draw.rect(screen, col, (sx, sy, 16, 16), border_radius=3)
            lbl = font_tiny.render(desc, True, WHITE)
            screen.blit(lbl, (sx + 24, sy))

        draw_centered_text(screen, "Player 1 (Blue)  --  W A S D", font_small, BLUE_LIGHT, 370)
        draw_centered_text(screen, "Player 2 (Red)   --  Arrow Keys", font_small, RED_LIGHT, 398)
        draw_centered_text(screen, "Press  SPACE  to start", font_small, GREEN, 440)
        draw_centered_text(screen, "Press  ESC  to quit",    font_tiny,  GRAY,  472)

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: return
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()
        clock.tick(FPS)


# ══════════════════════════════════════════════════════════
#  SCREEN: GAME OVER
# ══════════════════════════════════════════════════════════
def show_game_over_screen(winner_name, p1_score, p2_score, was_sudden_death):
    while True:
        screen.fill(BG_COLOR)
        draw_centered_text(screen, "TIME'S UP!", font_big, RED, 100)
        if was_sudden_death:
            draw_centered_text(screen, "SUDDEN DEATH!", font_medium, ORANGE, 162)
        draw_centered_text(screen, f"{winner_name} wins!", font_big, YELLOW, 200)
        draw_centered_text(screen, f"Player 1: {p1_score}   |   Player 2: {p2_score}",
                           font_medium, WHITE, 275)
        draw_centered_text(screen, "Press  SPACE  to play again", font_small, GREEN, 345)
        draw_centered_text(screen, "Press  ESC  to quit",         font_tiny,  GRAY,  382)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE: return True
                if event.key == pygame.K_ESCAPE: return False
        clock.tick(FPS)


# ══════════════════════════════════════════════════════════
#  SCREEN: SUDDEN DEATH
# ══════════════════════════════════════════════════════════
def show_sudden_death_screen():
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < 2200:
        screen.fill(BG_COLOR)
        draw_centered_text(screen, "IT'S A TIE!", font_big, YELLOW, 190)
        draw_centered_text(screen, "SUDDEN DEATH!", font_big, RED,   260)
        draw_centered_text(screen, "First tag wins!", font_medium, WHITE, 325)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        clock.tick(FPS)


# ══════════════════════════════════════════════════════════
#  MAIN GAME LOOP
# ══════════════════════════════════════════════════════════
def run_game(sudden_death=False):
    obstacles    = create_obstacles()
    power_cubes  = []          # list of PowerCube objects
    last_spawn   = pygame.time.get_ticks()

    player1 = Player(
        x=100, y=300,
        color=BLUE, color_dark=BLUE_DARK, color_light=BLUE_LIGHT,
        name="Player 1",
        controls={'up': pygame.K_w, 'down': pygame.K_s,
                  'left': pygame.K_a, 'right': pygame.K_d}
    )
    player2 = Player(
        x=660, y=300,
        color=RED, color_dark=RED_DARK, color_light=RED_LIGHT,
        name="Player 2",
        controls={'up': pygame.K_UP, 'down': pygame.K_DOWN,
                  'left': pygame.K_LEFT, 'right': pygame.K_RIGHT}
    )

    player1.is_chaser = True

    total_seconds = SUDDEN_DEATH_TIME if sudden_death else GAME_DURATION
    start_ticks   = pygame.time.get_ticks()
    tag_cooldown  = 0
    tag_flash     = 0
    collect_msg   = ""     # e.g. "P1 got SPEED!"
    collect_timer = 0      # frames to show the collect message

    # Spawn 2 cubes at the start
    for _ in range(2):
        cube = spawn_power_cube(obstacles, power_cubes)
        if cube:
            power_cubes.append(cube)

    while True:

        # ── Events ────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

        # ── Timer ─────────────────────────────────────────
        elapsed      = (pygame.time.get_ticks() - start_ticks) / 1000
        seconds_left = max(0, total_seconds - elapsed)

        # ── Spawn a new cube every CUBE_SPAWN_INTERVAL seconds ──
        now = pygame.time.get_ticks()
        if now - last_spawn >= CUBE_SPAWN_INTERVAL * 1000:
            alive_count = sum(1 for c in power_cubes if c.alive)
            if alive_count < 4:   # max 4 cubes on screen at once
                cube = spawn_power_cube(obstacles, power_cubes)
                if cube:
                    power_cubes.append(cube)
            last_spawn = now

        # ── Update power-up bob animation ─────────────────
        for cube in power_cubes:
            cube.update()

        # ── Movement ──────────────────────────────────────
        keys = pygame.key.get_pressed()
        player1.move(keys, obstacles)
        player2.move(keys, obstacles)
        player1.update_powerup()
        player2.update_powerup()

        # ── Power cube collection ─────────────────────────
        for cube in power_cubes:
            if not cube.alive:
                continue

            for player in (player1, player2):
                if player.rect.colliderect(cube.rect):
                    cube.alive = False

                    if cube.kind == "swap":
                        # Instantly swap who is the chaser
                        player1.is_chaser = not player1.is_chaser
                        player2.is_chaser = not player2.is_chaser
                        collect_msg   = f"{player.name} used SWAP!"
                    else:
                        player.apply_powerup(cube.kind)
                        label = POWERUP_TYPES[cube.kind]["label"]
                        collect_msg = f"{player.name} got {label}!"

                    collect_timer = 120   # show message for 2 seconds
                    break

        if collect_timer > 0:
            collect_timer -= 1

        # ── Tag detection ─────────────────────────────────
        if tag_cooldown > 0:
            tag_cooldown -= 1
        else:
            chaser  = player1 if player1.is_chaser else player2
            runner  = player2 if player1.is_chaser else player1

            # Shielded runner cannot be tagged
            if chaser.rect.colliderect(runner.rect) and not runner.is_shielded:
                chaser.score += 1

                player1.is_chaser = not player1.is_chaser
                player2.is_chaser = not player2.is_chaser

                tag_cooldown = TAG_COOLDOWN_FRAMES
                tag_flash    = TAG_COOLDOWN_FRAMES

                if sudden_death:
                    winner = player1 if player1.score > player2.score else player2
                    return winner.name, player1.score, player2.score, True

        if tag_flash > 0:
            tag_flash -= 1

        # ── Time up ───────────────────────────────────────
        if seconds_left <= 0:
            if player1.score == player2.score:
                return "TIE", player1.score, player2.score, False
            winner = player1 if player1.score > player2.score else player2
            return winner.name, player1.score, player2.score, False

        # ══ DRAW ══════════════════════════════════════════
        screen.fill(BG_COLOR)

        # Grid
        for x in range(0, SCREEN_WIDTH, 80):
            pygame.draw.line(screen, (38, 38, 52), (x, ARENA_TOP), (x, SCREEN_HEIGHT))
        for y in range(ARENA_TOP, SCREEN_HEIGHT, 80):
            pygame.draw.line(screen, (38, 38, 52), (0, y), (SCREEN_WIDTH, y))

        # Obstacles
        for obs in obstacles:
            obs.draw(screen)

        # Power cubes
        for cube in power_cubes:
            cube.draw(surface=screen)

        # Players
        player1.draw(screen)
        player2.draw(screen)

        # "TAGGED!" flash
        if tag_flash > 0:
            alpha    = int(255 * (tag_flash / TAG_COOLDOWN_FRAMES))
            msg_surf = font_big.render("TAGGED!", True, GREEN)
            msg_surf.set_alpha(alpha)
            screen.blit(msg_surf,
                        ((SCREEN_WIDTH - msg_surf.get_width()) // 2,
                         SCREEN_HEIGHT // 2 - 30))

        # Power-up collect message
        if collect_timer > 0:
            alpha = min(255, collect_timer * 3)
            cm_surf = font_medium.render(collect_msg, True, YELLOW)
            cm_surf.set_alpha(alpha)
            screen.blit(cm_surf,
                        ((SCREEN_WIDTH - cm_surf.get_width()) // 2,
                         SCREEN_HEIGHT // 2 + 40))

        # ── HUD bar ───────────────────────────────────────
        pygame.draw.rect(screen, HUD_COLOR, (0, 0, SCREEN_WIDTH, 65))
        pygame.draw.line(screen, DARK_GRAY, (0, 65), (SCREEN_WIDTH, 65), 1)

        # P1 info
        p1_name_surf  = font_medium.render("P1  WASD",         True, BLUE)
        p1_score_surf = font_medium.render(str(player1.score), True, WHITE)
        screen.blit(p1_name_surf,  (14,  5))
        screen.blit(p1_score_surf, (14, 33))

        # P1 active power-up badge
        if player1.powerup:
            info  = POWERUP_TYPES[player1.powerup]
            badge = font_tiny.render(info["label"], True, info["color"])
            screen.blit(badge, (14 + p1_score_surf.get_width() + 8, 38))

        # P2 info
        p2_name_surf  = font_medium.render("P2  Arrows",        True, RED)
        p2_score_surf = font_medium.render(str(player2.score),  True, WHITE)
        screen.blit(p2_name_surf,  (SCREEN_WIDTH - p2_name_surf.get_width()  - 14,  5))
        screen.blit(p2_score_surf, (SCREEN_WIDTH - p2_score_surf.get_width() - 14, 33))

        # P2 active power-up badge
        if player2.powerup:
            info  = POWERUP_TYPES[player2.powerup]
            badge = font_tiny.render(info["label"], True, info["color"])
            screen.blit(badge,
                        (SCREEN_WIDTH - p2_score_surf.get_width() - badge.get_width() - 22, 38))

        # Centre: countdown timer
        secs = int(seconds_left)
        if sudden_death:
            timer_color = RED if (secs % 2 == 0) else ORANGE
        elif secs <= 10: timer_color = RED
        elif secs <= 20: timer_color = ORANGE
        else:            timer_color = WHITE

        timer_surf = font_medium.render(f"{secs}s", True, timer_color)
        screen.blit(timer_surf,
                    (SCREEN_WIDTH // 2 - timer_surf.get_width() // 2, 5))

        if sudden_death:
            sub = font_tiny.render("SUDDEN DEATH", True, ORANGE)
        else:
            chaser = player1 if player1.is_chaser else player2
            sub    = font_tiny.render(f"{chaser.name} is chasing!", True, YELLOW)
        screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 35))

        draw_timer_bar(screen, seconds_left, total_seconds, sudden_death)

        # Legend
        draw_powerup_legend(screen)

        pygame.display.flip()
        clock.tick(FPS)


# ══════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════
def main():
    show_start_screen()

    while True:
        winner, p1, p2, was_sd = run_game(sudden_death=False)

        if winner == "TIE":
            show_sudden_death_screen()
            winner, p1, p2, was_sd = run_game(sudden_death=True)

        play_again = show_game_over_screen(winner, p1, p2, was_sd)
        if not play_again:
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
