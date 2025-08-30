from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import random
import math
import time
import sys

# Window and arena parameters
WIN_W, WIN_H = 1000, 800
GRID_SIZE = 600
WALL_HEIGHT = 80

# Player parameters
PLAYER_RADIUS = 30
PLAYER_SPEED = 10
ROT_SPEED = 5
px, pz = 0, 0    # player position XZ
p_angle = 0      # facing angle degrees
p_color = (random.random(), random.random(), random.random())

# Camera position
cam_x, cam_y, cam_z = 0, 500, 800

# Gameplay variables
lives = 5
score = 0
keys_collected = 0
game_paused = False
cheat_mode = False

# Treasure & Key constants
NUM_TREASURES = 6
NUM_KEYS = 4
KEY_RADIUS = 8

# Treasure types definitions
TREASURE_TYPES = {
    'gold': {'points': 15, 'size': 40, 'color': (1.0, 0.84, 0.0)},
    'silver': {'points': 10, 'size': 30, 'color': (0.75, 0.75, 0.75)},
    'diamond': {'points': 25, 'size': 50, 'color': (0.0, 1.0, 1.0)},
}

# Enemies parameters
NUM_ENEMIES = 3
ENEMY_RADIUS = 20
ENEMY_INITIAL_SPEED = 2
ENEMY_SPEED_INCREMENT = 0.5
SPEED_INCREASE_INTERVAL = 30  # seconds

# Global containers
keys = []
treasures = []
enemies = []

# Timers
start_time = None

# Button parameters and positions (top-right corner)
BUTTON_SIZE = 40
BUTTON_MARGIN = 10
buttons = {
    'restart': (WIN_W - 3 * (BUTTON_SIZE + BUTTON_MARGIN), WIN_H - BUTTON_SIZE - BUTTON_MARGIN, BUTTON_SIZE, BUTTON_SIZE),
    'pause': (WIN_W - 2 * (BUTTON_SIZE + BUTTON_MARGIN), WIN_H - BUTTON_SIZE - BUTTON_MARGIN, BUTTON_SIZE, BUTTON_SIZE),
    'exit': (WIN_W - (BUTTON_SIZE + BUTTON_MARGIN), WIN_H - BUTTON_SIZE - BUTTON_MARGIN, BUTTON_SIZE, BUTTON_SIZE),
}

# Global variable to store window ID for proper destruction on quit
window_id = None

def random_position(margin=100):
    return (
        random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin),
        random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
    )

def init_game():
    global keys, treasures, enemies, lives, score, keys_collected, px, pz, p_angle, start_time, game_paused, cheat_mode

    lives = 5
    score = 0
    keys_collected = 0
    px, pz = 0, 0
    p_angle = 0
    game_paused = False
    cheat_mode = False

    # Initialize treasures
    treasures.clear()
    treasure_types_list = list(TREASURE_TYPES.keys())
    for _ in range(NUM_TREASURES):
        x, z = random_position()
        ttype = random.choice(treasure_types_list)
        treasures.append({'x': x, 'z': z, 'type': ttype, 'opened': False})

    # Initialize keys
    keys.clear()
    for _ in range(NUM_KEYS):
        x, z = random_position()
        keys.append({'x': x, 'z': z, 'collected': False})

    # Initialize enemies with rectangular patrol paths
    enemies.clear()
    for i in range(NUM_ENEMIES):
        margin = 200
        x1 = random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
        z1 = random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
        size = random.uniform(150, 250)
        x2 = x1 + size
        z2 = z1 + size

        path = [
            (x1, z1),
            (x2, z1),
            (x2, z2),
            (x1, z2)
        ]
        enemies.append({
            'path': path,
            'pos': list(path[0]),
            'speed': ENEMY_INITIAL_SPEED,
            'dir_index': 0
        })

    start_time = time.time()

def distance(x1, z1, x2, z2):
    return math.sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2)

# Drawing helper functions

def draw_rect(x, y, w, h):
    """Draw rectangle outline with GL_LINE_LOOP."""
    glBegin(GL_LINE_LOOP)
    glVertex2i(x, y)
    glVertex2i(x + w, y)
    glVertex2i(x + w, y + h)
    glVertex2i(x, y + h)
    glEnd()

def draw_button(x, y, w, h, color, label, paused_state=False):
    """Draw a UI button with distinct icons."""
    glColor3f(*color)
    draw_rect(x, y, w, h)
    cx = x + w // 2
    cy = y + h // 2
    glColor3f(*color)

    if label == 'restart':
        # Draw left arrow inside rectangle for restart
        glBegin(GL_LINES)
        glVertex2i(cx + 10, cy + 12)
        glVertex2i(cx - 8, cy)
        glVertex2i(cx - 8, cy)
        glVertex2i(cx + 10, cy - 12)
        glEnd()
    elif label == 'pause':
        # Draw pause bars; change color if paused
        bar_color = (0.0, 0.7, 0.0) if not paused_state else (0.4, 0.4, 0.4)
        glColor3f(*bar_color)
        glBegin(GL_QUADS)
        glVertex2i(cx - 8, cy + 12)
        glVertex2i(cx - 4, cy + 12)
        glVertex2i(cx - 4, cy - 12)
        glVertex2i(cx - 8, cy - 12)

        glVertex2i(cx + 4, cy + 12)
        glVertex2i(cx + 8, cy + 12)
        glVertex2i(cx + 8, cy - 12)
        glVertex2i(cx + 4, cy - 12)
        glEnd()
    elif label == 'exit':
        # Red cross icon for exit
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2i(cx - 12, cy - 12)
        glVertex2i(cx + 12, cy + 12)
        glVertex2i(cx + 12, cy - 12)
        glVertex2i(cx - 12, cy + 12)
        glEnd()

def draw_grid():
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_LINES)
    for i in range(-GRID_SIZE, GRID_SIZE + 1, 40):
        glVertex3f(i, -GRID_SIZE, 0)
        glVertex3f(i, GRID_SIZE, 0)
        glVertex3f(-GRID_SIZE, i, 0)
        glVertex3f(GRID_SIZE, i, 0)
    glEnd()

def draw_walls():
    glColor3f(0.3, 0.3, 0.3)
    for tx, ty in [(0, GRID_SIZE + 5), (0, -GRID_SIZE - 5)]:
        glPushMatrix()
        glTranslatef(tx, ty, WALL_HEIGHT / 2)
        glScalef(GRID_SIZE * 2 + 10, 10, WALL_HEIGHT)
        glutSolidCube(1)
        glPopMatrix()
    for tx, ty in [(-GRID_SIZE - 5, 0), (GRID_SIZE + 5, 0)]:
        glPushMatrix()
        glTranslatef(tx, ty, WALL_HEIGHT / 2)
        glScalef(10, GRID_SIZE * 2 + 10, WALL_HEIGHT)
        glutSolidCube(1)
        glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(px, pz, PLAYER_RADIUS)
    glRotatef(p_angle, 0, 0, 1)

    glColor3f(*p_color)
    quad = gluNewQuadric()
    gluSphere(quad, PLAYER_RADIUS, 20, 20)

    glColor3f(0.2, 0.8, 0.2)
    glTranslatef(40, 0, 0)
    glRotatef(90, 0, 1, 0)
    gluCylinder(quad, 10, 5, 50, 20, 20)

    glPopMatrix()

def draw_keys():
    for key in keys:
        if not key['collected'] or cheat_mode:
            glPushMatrix()
            glTranslatef(key['x'], key['z'], KEY_RADIUS)
            glColor3f(1.0, 1.0, 0.0)
            quad = gluNewQuadric()
            gluSphere(quad, KEY_RADIUS, 10, 10)
            glPopMatrix()

def draw_treasures():
    for treasure in treasures:
        if not treasure['opened']:
            props = TREASURE_TYPES[treasure['type']]
            size, color = props['size'], props['color']
            glPushMatrix()
            glTranslatef(treasure['x'], treasure['z'], size / 2)
            glColor3f(*color)
            glScalef(size, size, size)
            glutSolidCube(1)
            glPopMatrix()

def draw_enemies():
    for enemy in enemies:
        glPushMatrix()
        glTranslatef(enemy['pos'][0], enemy['pos'][1], ENEMY_RADIUS)
        glColor3f(1.0, 0.0, 0.0)
        quad = gluNewQuadric()
        gluSphere(quad, ENEMY_RADIUS, 20, 20)
        glPopMatrix()

def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1,1,1)

    hud_text = f"Lives: {lives}    Keys: {keys_collected}    Score: {score}    " \
               f"{'[PAUSED]' if game_paused else ''} {'[CHEAT]' if cheat_mode else ''}"
    glRasterPos2f(20, WIN_H - 40)
    for ch in hud_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Draw buttons on HUD overlay
    draw_button(*buttons['restart'], (0.0, 0.7, 0.7), 'restart')
    draw_button(*buttons['pause'], (0.0, 0.7, 0.0), 'pause', paused_state=game_paused)
    draw_button(*buttons['exit'], (1.0, 0.0, 0.0), 'exit')

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

# Game logic

def player_collect_keys():
    global keys_collected
    if game_paused:
        return
    for key in keys:
        if not key['collected']:
            if distance(px, pz, key['x'], key['z']) < PLAYER_RADIUS + KEY_RADIUS:
                key['collected'] = True
                keys_collected += 1
                print(f"Collected a key! Total keys: {keys_collected}")

def player_open_treasure():
    global keys_collected, score
    if game_paused:
        return
    for treasure in treasures:
        if not treasure['opened']:
            if distance(px, pz, treasure['x'], treasure['z']) < PLAYER_RADIUS + TREASURE_TYPES[treasure['type']]['size'] / 2:
                if keys_collected > 0:
                    treasure['opened'] = True
                    keys_collected -= 1
                    score += TREASURE_TYPES[treasure['type']]['points']
                    print(f"Opened {treasure['type']} treasure! Score: {score}, Keys left: {keys_collected}")
                    break

def enemy_patrol_update(enemy, dt):
    path = enemy['path']
    dir_idx = enemy['dir_index']
    speed = enemy['speed']

    current_pos = enemy['pos']
    target_idx = (dir_idx + 1) % len(path)
    target_pos = path[target_idx]

    dx = target_pos[0] - current_pos[0]
    dz = target_pos[1] - current_pos[1]
    dist = math.sqrt(dx * dx + dz * dz)

    if dist < speed * dt:
        enemy['pos'] = [target_pos[0], target_pos[1]]
        enemy['dir_index'] = target_idx
    else:
        move_x = (dx / dist) * speed * dt
        move_z = (dz / dist) * speed * dt
        enemy['pos'][0] += move_x
        enemy['pos'][1] += move_z

def check_enemy_collision():
    global lives, game_paused
    if game_paused:
        return
    for enemy in enemies:
        if distance(px, pz, enemy['pos'][0], enemy['pos'][1]) < PLAYER_RADIUS + ENEMY_RADIUS:
            lives -= 1
            print(f"Hit by enemy! Lives left: {lives}")
            reset_player()
            if lives <= 0:
                print("Game Over!")
                game_paused = True
            break

def reset_player():
    global px, pz, p_angle
    px, pz = 0, 0
    p_angle = 0

def update_enemy_speeds():
    elapsed = time.time() - start_time
    increments = int(elapsed // SPEED_INCREASE_INTERVAL)
    for enemy in enemies:
        enemy['speed'] = ENEMY_INITIAL_SPEED + increments * ENEMY_SPEED_INCREMENT

def move_player(forward):
    if game_paused:
        return
    global px, pz
    rad = math.radians(p_angle)
    nx = px + math.cos(rad) * PLAYER_SPEED * forward
    nz = pz + math.sin(rad) * PLAYER_SPEED * forward
    boundary = GRID_SIZE - 70
    if -boundary < nx < boundary:
        px = nx
    if -boundary < nz < boundary:
        pz = nz
    player_collect_keys()

def keyboard(key, x, y):
    global p_angle, game_paused, cheat_mode
    key = key.decode("utf-8").lower()

    if key == 'w':
        move_player(1)
    elif key == 's':
        move_player(-1)
    elif key == 'a':
        p_angle = (p_angle + ROT_SPEED) % 360
    elif key == 'd':
        p_angle = (p_angle - ROT_SPEED) % 360
    elif key == 'e':
        player_open_treasure()
    elif key == 'p':
        game_paused = not game_paused
        print("Game paused." if game_paused else "Game resumed.")
    elif key == 'r':
        print("Restarting game...")
        init_game()
    elif key == 'c':
        cheat_mode = not cheat_mode
        print("Cheat mode toggled", "ON" if cheat_mode else "OFF")
    glutPostRedisplay()

def point_in_rect(px_, py_, rx, ry, rw, rh):
    return rx <= px_ <= rx + rw and ry <= py_ <= ry + rh

def on_mouse_click(button, state_click, x, y):
    global game_paused, window_id
    mouse_x = x
    mouse_y = WIN_H - y

    if state_click == GLUT_DOWN:
        for bname, (bx, by, bw, bh) in buttons.items():
            if point_in_rect(mouse_x, mouse_y, bx, by, bw, bh):
                if bname == 'restart':
                    print("Restarting game...")
                    init_game()
                elif bname == 'pause':
                    game_paused = not game_paused
                    print("Game paused." if game_paused else "Game resumed.")
                elif bname == 'exit':
                    print(f"Goodbye! Final score: {score}")
                    sys.stdout.flush()
                    time.sleep(0.1)
                    if window_id is not None:
                        glutDestroyWindow(window_id)
                    sys.exit(0)
                break

# Main loop update

last_update_time = None

def update(value=0):
    global last_update_time
    if last_update_time is None:
        last_update_time = time.time()
        glutTimerFunc(16, update, 0)
        return

    current_time = time.time()
    dt = current_time - last_update_time
    last_update_time = current_time

    if not game_paused:
        update_enemy_speeds()
        for enemy in enemies:
            enemy_patrol_update(enemy, dt)
        check_enemy_collision()

    glutPostRedisplay()
    glutTimerFunc(16, update, 0)

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70, WIN_W / WIN_H, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    setup_camera()

    draw_grid()
    draw_walls()
    draw_keys()
    draw_treasures()
    draw_enemies()
    draw_player()
    draw_hud()
    glutSwapBuffers()

def idle():
    glutPostRedisplay()

def main():
    global start_time, window_id
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(100, 50)
    window_id = glutCreateWindow(b"3D Treasure Hunt Arena - Full Features")

    init_game()

    glClearColor(0.1, 0.1, 0.1, 1)

    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutMouseFunc(on_mouse_click)
    glutTimerFunc(16, update, 0)

    glEnable(GL_DEPTH_TEST)

    start_time = time.time()

    glutMainLoop()

if __name__ == "__main__":
    main()
