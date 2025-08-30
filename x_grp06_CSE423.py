from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import random, math, time, sys

# ---------- Window & Player ----------
WIN_W, WIN_H = 1000, 800
GRID_SIZE = 600
PLAYER_RADIUS = 30
PLAYER_HEIGHT = 50
PLAYER_SPEED = 8
px, pz = 0.0, 0.0

# Camera
cam_x, cam_y, cam_z = 0, 500, 800

# Gameplay variables
frozen_until = 0
current_message = ""
message_display_time = 0
spike_phase = 0
key_bounce_phase = 0
score = 0
keys_collected = 0
lives = 3
max_lives = 10
diamond_spin_angle = 0
diamond_bounce_phase = 0
game_paused = False
last_frame_time = 0
FRAME_RATE = 60
game_start_time = 0
game_time = 0
freeze_start_time = 0
freeze_duration = 0
game_over = False
high_score = 0
TIME_LIMIT = 120  # 2 minutes time limit
paused_time_accumulated = 0
pause_start_time = 0
 

# UI Button definitions
RESTART_BUTTON = {"x": WIN_W - 150, "y": 20, "width": 60, "height": 30}
EXIT_BUTTON   = {"x": WIN_W -  80, "y": 20, "width": 50, "height": 30}
HOLD_BUTTON   = {"x": WIN_W - 220, "y": 20, "width": 60, "height": 30}

# ---------- Game Objects ----------
keys, treasures, obstacles, enemies, hearts = [], [], [], [], []
traps = []
trap_spike_scales = []

NUM_DIAMONDS = 5
NUM_KEYS = 5
NUM_OBSTACLES = 6
NUM_ENEMIES = 8
NUM_HEARTS = 3
KEY_RADIUS = 8
TREASURE_POINTS = 30
DIAMOND_POINTS = 25
HEART_RADIUS = 12
ENEMY_RADIUS = 25
ENEMY_MIN_SPEED = 1.0
ENEMY_MAX_SPEED = 6.0
ENEMY_SPEED_INCREMENT = 0.001
TRAP_RADIUS = 30

# Treasure types
TREASURE_TYPES = {
    'gold':    {'size': 40, 'color': (1.0, 0.5, 0.0)},
    'diamond': {'size': 50, 'color': (0.0, 0.8, 0.8)}
}

# ---------- Helper Functions ----------
def random_position(margin=150):
    return (random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin),
            random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin))

def distance(x1, z1, x2, z2):
    return math.hypot(x1 - x2, z1 - z2)

def is_valid_position(new_x, new_z, objects, min_distance=80):
    for obj in objects:
        if distance(new_x, new_z, obj['x'], obj['z']) < min_distance:
            return False
    return True

def init_traps():
    global traps
    traps = []
    existing_objects = []
    for _ in range(5):
        valid_position = False
        attempts = 0
        while not valid_position and attempts < 50:
            tx, tz = random_position(100)
            if is_valid_position(tx, tz, existing_objects, 100):
                traps.append({'x': tx, 'z': tz, 'active': True, 'cooldown': 0})
                existing_objects.append({'x': tx, 'z': tz})
                valid_position = True
            attempts += 1


# ---------- Pause Toggle ----------
def toggle_pause():
    global game_paused, pause_start_time, paused_time_accumulated
    if not game_paused:
        # Pause game
        game_paused = True
        pause_start_time = time.time()
    else:
        # Resume game
        game_paused = False
        paused_time_accumulated += time.time() - pause_start_time



# ---------- INPUT HANDLER ----------
def handle_movement(key, x, y):
    global px, pz
    if key == b'\x1b':  # ESC
      glutDestroyWindow(glutGetWindow())
      sys.exit()
      return

    # After game over: ONLY R works
    if game_over:
        if key in [b'r', b'R']:
            init_game()
        return

    if time.time() < frozen_until:
        return

    nx, nz = px, pz
    if   key in [b'w', b'W']: nz += PLAYER_SPEED
    elif key in [b's', b'S']: nz -= PLAYER_SPEED
    elif key in [b'a', b'A']: nx -= PLAYER_SPEED
    elif key in [b'd', b'D']: nx += PLAYER_SPEED
    elif key in [b'r', b'R']: init_game()

    elif key == b' ':  # SPACE toggles pause
        toggle_pause()
        return

    if check_boundary_wall_collision(nx, nz): return
    if check_obstacle_collision(nx, nz): return
    px, pz = nx, nz

def mouse_click(button, state, x, y):
    # Ignore all mouse input after game over
    if game_over:
        return

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        y = WIN_H - y
        if (RESTART_BUTTON["x"] <= x <= RESTART_BUTTON["x"] + RESTART_BUTTON["width"] and
            RESTART_BUTTON["y"] <= y <= RESTART_BUTTON["y"] + RESTART_BUTTON["height"]):
            init_game()
        elif (EXIT_BUTTON["x"] <= x <= EXIT_BUTTON["x"] + EXIT_BUTTON["width"] and
              EXIT_BUTTON["y"] <= y <= EXIT_BUTTON["y"] + EXIT_BUTTON["height"]):
            exit_game()
        elif (HOLD_BUTTON["x"] <= x <= HOLD_BUTTON["x"] + HOLD_BUTTON["width"] and
              HOLD_BUTTON["y"] <= y <= HOLD_BUTTON["y"] + HOLD_BUTTON["height"]):
            toggle_pause()
            glutPostRedisplay()

def idle_func():
    glutPostRedisplay()

# ---------- DISPLAY (UI helpers) ----------
def draw_grid():
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_LINES)
    for i in range(-GRID_SIZE, GRID_SIZE+1, 40):
        glVertex3f(i, -GRID_SIZE, 0); glVertex3f(i, GRID_SIZE, 0)
        glVertex3f(-GRID_SIZE, i, 0); glVertex3f(GRID_SIZE, i, 0)
    glEnd()

def draw_human_character():
    glPushMatrix()
    glTranslatef(px, pz, PLAYER_HEIGHT/2)  # position player

    # Body
    glPushMatrix()
    glColor3f(0.2, 0.6, 0.9)
    glScalef(PLAYER_RADIUS*1.2, PLAYER_RADIUS*0.6, PLAYER_HEIGHT*0.8)
    glutSolidCube(1)
    glPopMatrix()

    # Head
    glPushMatrix()
    glColor3f(1.0, 0.8, 0.6)
    glTranslatef(0, 0, PLAYER_HEIGHT*0.9)
    quad = gluNewQuadric()
    gluSphere(quad, PLAYER_RADIUS*0.5, 16, 16)
    glPopMatrix()

    # Left Arm
    glPushMatrix()
    glColor3f(0.2, 0.6, 0.9)
    glTranslatef(-PLAYER_RADIUS*0.9, 0, PLAYER_HEIGHT*0.4)
    glScalef(PLAYER_RADIUS*0.4, PLAYER_RADIUS*0.4, PLAYER_HEIGHT*0.6)
    glutSolidCube(1)
    glPopMatrix()

    # Right Arm
    glPushMatrix()
    glColor3f(0.2, 0.6, 0.9)
    glTranslatef(PLAYER_RADIUS*0.9, 0, PLAYER_HEIGHT*0.4)
    glScalef(PLAYER_RADIUS*0.4, PLAYER_RADIUS*0.4, PLAYER_HEIGHT*0.6)
    glutSolidCube(1)
    glPopMatrix()

    # Left Leg
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.8)
    glTranslatef(-PLAYER_RADIUS*0.4, 0, -PLAYER_HEIGHT*0.2)
    glScalef(PLAYER_RADIUS*0.5, PLAYER_RADIUS*0.5, PLAYER_HEIGHT*0.5)
    glutSolidCube(1)
    glPopMatrix()

    # Right Leg
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.8)
    glTranslatef(PLAYER_RADIUS*0.4, 0, -PLAYER_HEIGHT*0.2)
    glScalef(PLAYER_RADIUS*0.5, PLAYER_RADIUS*0.5, PLAYER_HEIGHT*0.5)
    glutSolidCube(1)
    glPopMatrix()

    glPopMatrix()

def draw_keys():
    global key_bounce_phase
    for key in keys:
        if not key['collected']:
            glPushMatrix()
            bounce = math.sin(key_bounce_phase) * 8
            glTranslatef(key['x'], key['z'], KEY_RADIUS + 5 + bounce)
            glColor3f(1.0, 0.9, 0.0)
            # Shaft
            glPushMatrix()
            glScalef(25, 5, 5)
            glutSolidCube(1)
            glPopMatrix()
            # Head
            glPushMatrix()
            glTranslatef(12.5, 0, 0)
            glScalef(10, 10, 4)
            glutSolidCube(1)
            glPopMatrix()
            # Tooth
            glPushMatrix()
            glTranslatef(-6, 0, 5)
            glScalef(7.5, 4, 4)
            glutSolidCube(1)
            glPopMatrix()
            glPopMatrix()

def draw_hearts():
    global key_bounce_phase
    for heart in hearts:
        if not heart['collected']:
            glPushMatrix()
            bounce = math.sin(key_bounce_phase * 1.2) * 6
            glTranslatef(heart['x'], heart['z'], HEART_RADIUS + bounce + 8)
            glow = 0.2 + 0.3 * math.sin(key_bounce_phase * 2)
            glColor3f(1.0, glow, glow)
            quad = gluNewQuadric()
            # Left
            glPushMatrix()
            glTranslatef(-HEART_RADIUS*0.3, 0, HEART_RADIUS*0.2)
            gluSphere(quad, HEART_RADIUS*0.6, 12, 12)
            glPopMatrix()
            # Right
            glPushMatrix()
            glTranslatef(HEART_RADIUS*0.3, 0, HEART_RADIUS*0.2)
            gluSphere(quad, HEART_RADIUS*0.6, 12, 12)
            glPopMatrix()
            # Bottom
            glPushMatrix()
            glTranslatef(0, 0, -HEART_RADIUS*0.2)
            glRotatef(45, 0, 1, 0)
            glScalef(HEART_RADIUS*0.8, HEART_RADIUS*0.4, HEART_RADIUS*0.8)
            glutSolidCube(1)
            glPopMatrix()
            glPopMatrix()

def draw_treasures():
    for tr in treasures:
        if tr['type'] == 'diamond':
            continue
        size  = 40 if tr['type']=='gold' else TREASURE_TYPES['diamond']['size']
        color = (0.8,0.5,0.2) if tr['type']=='gold' else TREASURE_TYPES['diamond']['color']
        glPushMatrix()
        glTranslatef(tr['x'], tr['z'], size/2)
        if tr['type']=='gold' and tr.get('opened',False):
            glColor3f(0.5,0.3,0.1)
            glScalef(size*0.8, size*0.8, size*0.5)
        else:
            glColor3f(*color)
            glScalef(size, size, size)
        glutSolidCube(1)
        glPopMatrix()

def draw_obstacles():
    for ox, oz, w, d, h in obstacles:
        glPushMatrix()
        glTranslatef(ox, oz, h/2)

        # Base
        glColor3f(0.4, 0.4, 0.45)
        glPushMatrix()
        glTranslatef(0, 0, -h*0.1)
        glScalef(w*1.5, d*1.5, h*0.1)
        glutSolidCube(1)
        glPopMatrix()

        # Pillar
        glColor3f(0.55, 0.55, 0.6)
        glPushMatrix()
        glScalef(w, d, h)
        glutSolidCube(1)
        glPopMatrix()

        # Cap
        glColor3f(0.8, 0.8, 0.85)
        glPushMatrix()
        glTranslatef(0, 0, h*0.5 + 5)
        glScalef(w*1.2, d*1.2, 10)
        glutSolidCube(1)
        glPopMatrix()

        # Decorative spheres
        glColor3f(0.7, 0.2, 0.2)
        num_spheres = 4
        sphere_radius = min(w, d) * 0.15
        quad = gluNewQuadric()
        for i in range(num_spheres):
            angle = i * (360 / num_spheres)
            rad = math.radians(angle)
            sx = (w*0.6) * math.cos(rad)
            sy = (d*0.6) * math.sin(rad)
            glPushMatrix()
            glTranslatef(sx, sy, h*0.25)
            gluSphere(quad, sphere_radius, 8, 8)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(sx * 0.8, sy * 0.8, h*0.75)
            gluSphere(quad, sphere_radius * 0.8, 8, 8)
            glPopMatrix()

        # Stripes
        glColor3f(0.3, 0.3, 0.35)
        stripe_width = w * 0.1
        for i in range(3):
            offset = (i - 1) * w * 0.3
            glPushMatrix()
            glTranslatef(offset, 0, 0)
            glScalef(stripe_width, d*1.01, h*1.01)
            glutSolidCube(1)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0, offset, 0)
            glScalef(w*1.01, stripe_width, h*1.01)
            glutSolidCube(1)
            glPopMatrix()

        glPopMatrix()

def draw_boundary_wall():
    brick_w, brick_d, brick_h = 40, 20, 20
    wall_height = 6
    gap = 2

    def draw_brick(x, y, z, sx, sy, sz):
        glColor3f(0.36, 0.18, 0.09)
        glPushMatrix()
        glTranslatef(x, y, z)
        glScalef(sx, sy, sz)
        glutSolidCube(1)
        glPopMatrix()
        glColor3f(0, 0, 0)
        glPushMatrix()
        glTranslatef(x, y, z + 0.51*sz)
        glScalef(sx*0.99, sy*0.99, 0.01)
        glBegin(GL_LINES)
        glVertex3f(-0.5, -0.5, 0); glVertex3f(0.5, -0.5, 0)
        glVertex3f(0.5, 0.5, 0);    glVertex3f(-0.5, 0.5, 0)
        glVertex3f(-0.5, -0.5, 0); glVertex3f(-0.5, 0.5, 0)
        glVertex3f(0.5, -0.5, 0);  glVertex3f(0.5, 0.5, 0)
        glEnd()
        glPopMatrix()

    def draw_wall(start_x, start_z, is_x_axis=True):
        for layer in range(wall_height):
            offset = (brick_w + gap)/2 if layer % 2 else 0
            for i in range(-GRID_SIZE, GRID_SIZE, brick_w + gap):
                if is_x_axis:
                    draw_brick(i + offset + brick_w/2, start_z, (layer + 0.5)*(brick_h+gap),
                               brick_w, brick_d, brick_h)
                else:
                    draw_brick(start_x, i + offset + brick_w/2, (layer + 0.5)*(brick_h+gap),
                               brick_d, brick_w, brick_h)

    draw_wall(0,  GRID_SIZE, True)
    draw_wall(0, -GRID_SIZE, True)
    draw_wall( GRID_SIZE, 0, False)
    draw_wall(-GRID_SIZE, 0, False)

def draw_traps():
    for trap in traps:
        glPushMatrix()
        glTranslatef(trap['x'], trap['z'], 0)

        # Base platform
        glColor3f(0.5, 0.0, 0.0)
        glPushMatrix()
        glTranslatef(0, 0, 5)
        glScalef(40, 40, 10)
        glutSolidCube(1)
        glPopMatrix()

        if trap['active']:
            glColor3f(1.0, 0.0, 0.0)
            glPushMatrix()
            glTranslatef(0, 0, 20)
            glScalef(30, 30, 40)
            glutSolidCube(1)
            glPopMatrix()
            glColor3f(0.8, 0.8, 0.0)
            quad = gluNewQuadric()
            for i in range(4):
                angle = i * 90
                rad = math.radians(angle)
                spike_x = 15 * math.cos(rad)
                spike_z = 15 * math.sin(rad)
                glPushMatrix()
                glTranslatef(spike_x, spike_z, 40)
                glRotatef(-90, 1, 0, 0)
                gluCylinder(quad, 5, 0, 15, 8, 2)
                glPopMatrix()
        else:
            glColor3f(0.3, 0.3, 0.3)
            glPushMatrix()
            glTranslatef(0, 0, 15)
            glScalef(25, 25, 30)
            glutSolidCube(1)
            glPopMatrix()
            glColor3f(0.0, 0.8, 0.0)
            glPushMatrix()
            glTranslatef(0, 0, 30)
            glScalef(20, 5, 5)
            glutSolidCube(1)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0, 0, 30)
            glScalef(5, 20, 5)
            glutSolidCube(1)
            glPopMatrix()

        glPopMatrix()

def draw_enemy(en):
    glPushMatrix()
    glTranslatef(en['x'], en['z'], ENEMY_RADIUS)
    glColor3f(0.8, 0.1, 0.1)
    quad = gluNewQuadric()
    gluSphere(quad, ENEMY_RADIUS, 16, 16)
    glColor3f(1.0, 0.2, 0.2)
    spike_length = ENEMY_RADIUS * 0.8
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x = math.cos(rad) * (ENEMY_RADIUS + spike_length/2)
        y = math.sin(rad) * (ENEMY_RADIUS + spike_length/2)
        glPushMatrix()
        glTranslatef(x, y, 0)
        glScalef(spike_length*0.2, spike_length*0.2, spike_length)
        glutSolidCube(1)
        glPopMatrix()
    glPopMatrix()

def draw_enemies():
    for en in enemies:
        draw_enemy(en)

# ---------- CAMERA ----------
def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70, WIN_W/float(WIN_H), 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)

# ---------- DIAMOND SHAPE FUNCTIONS ----------
def draw_diamond_shape():
    quad = gluNewQuadric()
    # Crown
    glPushMatrix()
    glTranslatef(0, 0, 0.1)
    glRotatef(180, 1, 0, 0)
    gluCylinder(quad, 0.8, 0.1, 0.6, 12, 1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 0.65)
    glScalef(0.2, 0.2, 0.03)
    glutSolidCube(1)
    glPopMatrix()
    # Girdle
    glPushMatrix()
    glTranslatef(0, 0, 0.0)
    glScalef(0.85, 0.85, 0.1)
    glutSolidCube(1)
    glPopMatrix()
    for i in range(6):
        angle = i * 60.0
        glPushMatrix()
        glRotatef(angle, 0, 0, 1)
        glTranslatef(0.75, 0, 0.0)
        glScalef(0.15, 0.08, 0.08)
        glutSolidCube(1)
        glPopMatrix()
    # Pavilion
    glPushMatrix()
    glTranslatef(0, 0, -0.05)
    gluCylinder(quad, 0.8, 0.0, 1.2, 12, 1)
    glPopMatrix()
    # Sparkle
    glPushMatrix()
    glTranslatef(0, 0, 0.7)
    gluSphere(quad, 0.05, 6, 6)
    glPopMatrix()

def draw_diamonds():
    global diamond_spin_angle, diamond_bounce_phase
    for tr in treasures:
        if tr['type'] != 'diamond' or tr.get('collected', False):
            continue
        base_size = 18
        glPushMatrix()
        bounce = math.sin(diamond_bounce_phase) * 12 + math.sin(diamond_bounce_phase * 1.5) * 4
        glTranslatef(tr['x'], tr['z'], base_size + bounce + 20)
        glRotatef(diamond_spin_angle, 0, 0, 1)
        glRotatef(diamond_spin_angle * 0.5, 1, 0, 0)
        glRotatef(diamond_spin_angle * 0.2, 0, 1, 0)
        pop_scale = 1.0 + 0.25 * math.sin(diamond_bounce_phase * 2.5) + 0.15 * math.sin(diamond_bounce_phase * 5)
        glScalef(base_size * pop_scale, base_size * pop_scale, base_size * pop_scale)
        shimmer = 0.15 + 0.25 * math.sin(diamond_bounce_phase * 3)
        pulse_color = 0.05 + 0.15 * math.sin(diamond_bounce_phase * 6)
        glColor3f(pulse_color + shimmer * 0.2, 0.75 + shimmer * 0.25, 0.9 + shimmer * 0.1)
        draw_diamond_shape()
        glPopMatrix()

# ---------- COLLISIONS ----------
def check_boundary_wall_collision(nx, nz):
    wall_thickness = 20
    player_collision_radius = PLAYER_RADIUS * 0.8
    if (nz + player_collision_radius > GRID_SIZE - wall_thickness and abs(nx) <= GRID_SIZE): return True
    if (nz - player_collision_radius < -GRID_SIZE + wall_thickness and abs(nx) <= GRID_SIZE): return True
    if (nx + player_collision_radius > GRID_SIZE - wall_thickness and abs(nz) <= GRID_SIZE): return True
    if (nx - player_collision_radius < -GRID_SIZE + wall_thickness and abs(nz) <= GRID_SIZE): return True
    return False

def check_obstacle_collision(nx, nz):
    px_half = PLAYER_RADIUS * 1.5 / 2
    pz_half = PLAYER_RADIUS * 1.5 / 2
    for ox, oz, w, d, h in obstacles:
        if abs(nx - ox) < w/2 + px_half and abs(nz - oz) < d/2 + pz_half:
            return True
    return False

def check_trap_collisions():
    global current_message, message_display_time, frozen_until, traps
    if time.time() < frozen_until:
        return False
    current_time = time.time()
    for trap in traps:
        if (distance(px, pz, trap['x'], trap['z']) < PLAYER_RADIUS + 20 and trap['active']):
            frozen_until = current_time + 3
            trap['active'] = False
            trap['cooldown'] = current_time + 2
            current_message = "TRAPPED! Frozen for 3 seconds"
            message_display_time = current_time
            return True
    return False

def check_enemy_collision():
    global current_message, message_display_time, frozen_until, lives, enemies, game_over, high_score
    for i, en in enumerate(enemies):
        if distance(px, pz, en['x'], en['z']) < PLAYER_RADIUS + ENEMY_RADIUS:
            attempts = 0
            while attempts < 20:
                new_x, new_z = random_position(200)
                if distance(new_x, new_z, px, pz) > 150:
                    en['x'], en['z'] = new_x, new_z
                    break
                attempts += 1
            angle = random.uniform(0, 2*math.pi)
            en['dx'], en['dz'] = math.cos(angle), math.sin(angle)
            lives -= 1
            if lives <= 0:
                lives = 0
                current_message = "Game Over! Press R to restart"
                message_display_time = time.time()
                # --- Freeze the game: set game_over and capture high_score
                game_over = True
                if score > high_score:
                    high_score = score
            else:
                current_message = f"Hit by Enemy! Lives: {lives}"
                message_display_time = time.time()
            return True
    return False

# ---------- COLLECTION ----------
def update_collection():
    global keys_collected, score, current_message, message_display_time, lives
    for key in keys:
        if not key['collected'] and distance(px, pz, key['x'], key['z']) < PLAYER_RADIUS + KEY_RADIUS:
            key['collected'] = True
            keys_collected += 1
            current_message = f"Key Found! Total: {keys_collected}"
            message_display_time = time.time()

    for tr in treasures:
        if tr['type']=='gold' and not tr.get('opened',False):
            if distance(px, pz, tr['x'], tr['z']) < PLAYER_RADIUS + 20:
                if keys_collected > 0:
                    tr['opened'] = True
                    keys_collected -= 1
                    old_score = score
                    score += TREASURE_POINTS
                    current_message = f"Treasure Opened! +{TREASURE_POINTS} points"
                    message_display_time = time.time()
                    increase_enemy_speed(old_score, score)
                else:
                    current_message = "Need a key to open treasure!"
                    message_display_time = time.time()

    for tr in treasures:
        if tr['type']=='diamond' and not tr.get('collected', False):
            if distance(px, pz, tr['x'], tr['z']) < PLAYER_RADIUS + 25:
                tr['collected'] = True
                old_score = score
                score += DIAMOND_POINTS
                current_message = f"Diamond Found! +{DIAMOND_POINTS} points"
                message_display_time = time.time()
                increase_enemy_speed(old_score, score)

    for heart in hearts:
        if not heart['collected'] and distance(px, pz, heart['x'], heart['z']) < PLAYER_RADIUS + HEART_RADIUS:
            if lives < max_lives:
                heart['collected'] = True
                lives += 1
                current_message = f"Heart Found! Lives: {lives}"
                message_display_time = time.time()
            else:
                heart['collected'] = True
                old_score = score
                score += 10
                current_message = "Max Hearts! +10 points"
                message_display_time = time.time()
                increase_enemy_speed(old_score, score)

def increase_enemy_speed(old_score, new_score):
    old_milestone = old_score // 50
    new_milestone = new_score // 50
    if new_milestone > old_milestone:
        speed_increase = 0.5 * (new_milestone - old_milestone)
        for enemy in enemies:
            enemy['speed'] = min(ENEMY_MAX_SPEED, enemy['speed'] + speed_increase)
        global current_message, message_display_time
        current_message += f" - Enemy Speed Increased!"
        message_display_time = time.time()

# ---------- ENEMIES ----------
def update_enemies():
    for en in enemies:
        new_x = en['x'] + en['dx'] * en['speed']
        new_z = en['z'] + en['dz'] * en['speed']
        if check_boundary_wall_collision(new_x, new_z):
            if check_boundary_wall_collision(en['x'] + en['dx'] * en['speed'], en['z']):
                en['dx'] *= -1
            if check_boundary_wall_collision(en['x'], en['z'] + en['dz'] * en['speed']):
                en['dz'] *= -1
            angle_adjust = random.uniform(-0.5, 0.5)
            new_angle = math.atan2(en['dz'], en['dx']) + angle_adjust
            en['dx'] = math.cos(new_angle)
            en['dz'] = math.sin(new_angle)
        else:
            en['x'] = new_x
            en['z'] = new_z
        en['speed'] = min(ENEMY_MAX_SPEED, en['speed'] + ENEMY_SPEED_INCREMENT)

# ---------- TRAP ANIMATION ----------
def update_traps():
    current_time = time.time()
    for trap in traps:
        if not trap['active'] and trap['cooldown'] < current_time:
            valid_position = False
            attempts = 0
            while not valid_position and attempts < 20:
                new_x, new_z = random_position(100)
                player_dist = distance(new_x, new_z, px, pz)
                too_close = False
                for other_trap in traps:
                    if other_trap != trap and other_trap['active']:
                        trap_dist = distance(new_x, new_z, other_trap['x'], other_trap['z'])
                        if trap_dist < 100:
                            too_close = True
                            break
                if player_dist > 150 and not too_close:
                    valid_position = True
                    trap['x'] = new_x
                    trap['z'] = new_z
                attempts += 1
            trap['active'] = True

# ---------- MESSAGES & UI ----------
def display_persistent_ui():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Score
    glColor3f(1, 1, 0)
    glRasterPos2f(20, WIN_H - 30)
    score_text = f"Score: {score}"
    for ch in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Lives
    glColor3f(1, 0.2, 0.2)
    glRasterPos2f(20, WIN_H - 60)
    lives_text = f"Lives: {lives}/{max_lives}"
    for ch in lives_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Heart symbols
    heart_spacing = 28
    for i in range(min(lives, 10)):
        x_pos = 20 + (i * heart_spacing)
        y_pos = WIN_H - 90
        glRasterPos2f(x_pos, y_pos)
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord('H'))

    # Keys
    glColor3f(1, 1, 0.3)
    glRasterPos2f(20, WIN_H - 120)
    keys_text = f"Keys: {keys_collected}"
    for ch in keys_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
    for i in range(keys_collected):
        x_pos = 90 + (i * 20)
        y_pos = WIN_H - 122
        glRasterPos2f(x_pos, y_pos)
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord('K'))

    # Controls
    glColor3f(0.8, 0.8, 0.8)
    glRasterPos2f(20, WIN_H - 160)
    controls_text = "Controls: WASD to move, SPACE to pause, R to restart, ESC to quit"
    for ch in controls_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    # Timer (uses frozen game_time after game over)
    glColor3f(0.5, 1.0, 0.5)
    glRasterPos2f(WIN_W - 200, WIN_H - 30)
    time_left = max(0, TIME_LIMIT - game_time)
    timer_text = f"Time: {int(time_left)}s"
    for ch in timer_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # Enemy speed info
    if enemies:
        avg_speed = sum(enemy['speed'] for enemy in enemies) / len(enemies)
        glColor3f(1, 0.3, 0.3)
        glRasterPos2f(WIN_W - 200, WIN_H - 60)
        speed_text = f"Enemy Speed: {avg_speed:.1f}"
        for ch in speed_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display_message():
    global current_message, message_display_time
    if current_message and time.time() - message_display_time < 2.5 and not game_over:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WIN_W, 0, WIN_H)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        if "Diamond Found" in current_message:
            glColor3f(0, 1, 1)
        elif "Heart Found" in current_message or "Max Hearts" in current_message:
            glColor3f(1, 0.5, 0.8)
        elif "Game Over" in current_message:
            glColor3f(1, 0, 0)
        elif "Hit by Enemy" in current_message or "TRAPPED" in current_message:
            glColor3f(1, 0.5, 0)
        elif "Key Found" in current_message:
            glColor3f(1, 1, 0)
        elif "Treasure Opened" in current_message:
            glColor3f(1, 0.8, 0)
        else:
            glColor3f(1, 0.6, 0)

        message_x = WIN_W/2 - len(current_message) * 5
        glRasterPos2f(message_x, WIN_H/2 + 50)
        for ch in current_message:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

def display_pause_message():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glColor3f(1, 1, 1)
    pause_text = "GAME PAUSED - Press SPACE / Click HOLD to continue"
    text_x = WIN_W/2 - len(pause_text) * 4
    glRasterPos2f(text_x, WIN_H/2)
    for ch in pause_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display_game_over_screen():
    global score, high_score

    # --- Update high score when game ends ---
    if score > high_score:
        high_score = score

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # --- Background (semi-transparent black box) ---
 

    # --- Title ---
    glColor3f(1, 0, 0)
    game_over_text = "GAME OVER"
    text_x = WIN_W/2 - len(game_over_text) * 9
    glRasterPos2f(text_x, WIN_H/2 + 70)
    for ch in game_over_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # --- Final Score ---
    glColor3f(1, 1, 0)
    score_text = f"Final Score: {score}"
    text_x = WIN_W/2 - len(score_text) * 9
    glRasterPos2f(text_x, WIN_H/2 + 25)
    for ch in score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # --- High Score ---
    glColor3f(0, 1, 1)
    high_score_text = f"High Score: {high_score}"
    text_x = WIN_W/2 - len(high_score_text) * 9
    glRasterPos2f(text_x, WIN_H/2 - 15)
    for ch in high_score_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    # --- Instruction ---
    glColor3f(1, 1, 1)
    restart_text = "Press R to play again"
    text_x = WIN_W/2 - len(restart_text) * 9
    glRasterPos2f(text_x, WIN_H/2 - 55)
    for ch in restart_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# ---------- ANIMATION ----------
def update_animations():
    global key_bounce_phase, diamond_spin_angle, diamond_bounce_phase
    if game_over:
        return  # stop animating after game over
    key_bounce_phase += 0.1
    diamond_spin_angle = (diamond_spin_angle + 3) % 360
    diamond_bounce_phase += 0.08

# ---------- DISPLAY ----------
def display():
    global frozen_until, last_frame_time, game_time, game_start_time, game_over, high_score

    current_time = time.time()
    # Frame limiter
    if current_time - last_frame_time < 1.0/FRAME_RATE:
        return
    last_frame_time = current_time

    # Freeze timer after game over
    if not game_over:
     if not game_paused:
        game_time = current_time - game_start_time - paused_time_accumulated


    # Time limit check
    if game_time >= TIME_LIMIT and not game_over:
        game_over = True
        if score > high_score:
            high_score = score

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    setup_camera()

    # Update logic only when active (not paused, not frozen, not game over)
    if not game_paused and current_time >= frozen_until and not game_over:
        update_animations()
        update_collection()
        update_enemies()
        update_traps()
        check_enemy_collision()
        check_trap_collisions()

    # Draw
    draw_grid()
    draw_boundary_wall()
    draw_treasures()
    draw_diamonds()
    draw_keys()
    draw_hearts()
    draw_obstacles()
    draw_traps()
    draw_enemies()
    draw_human_character()
    display_persistent_ui()
    display_message()

    if game_paused and not game_over:
        display_pause_message()
    if game_over:
        display_game_over_screen()

    glutSwapBuffers()

def reshape(w,h):
    global WIN_W, WIN_H
    WIN_W, WIN_H = w, h
    glViewport(0, 0, w, h)

# ---------- GAME INIT ----------
def init_game():
    global treasures, keys, obstacles, enemies, hearts, px, pz, trap_spike_scales, score, keys_collected, lives
    global current_message, message_display_time, frozen_until, traps, game_start_time, game_over, game_paused, game_time

    treasures.clear(); keys.clear(); obstacles.clear(); enemies.clear(); hearts.clear()
    px, pz = 0, 0
    score = 0; keys_collected = 0; lives = 3
    trap_spike_scales.clear()
    current_message = ""
    message_display_time = 0
    frozen_until = 0
    game_start_time = time.time()
    game_time = 0
    game_over = False
    game_paused = False

    # Traps first
    init_traps()

    # Gather occupied positions
    existing_objects = [{'x': t['x'], 'z': t['z']} for t in traps]

    # Gold treasures
    for _ in range(4):
        valid_position = False
        attempts = 0
        while not valid_position and attempts < 50:
            x, z = random_position()
            if is_valid_position(x, z, existing_objects, 80):
                treasures.append({'x': x, 'z': z, 'type': 'gold', 'opened': False})
                existing_objects.append({'x': x, 'z': z})
                valid_position = True
            attempts += 1

    # Diamonds
    for _ in range(NUM_DIAMONDS):
        valid_position = False
        attempts = 0
        while not valid_position and attempts < 50:
            x, z = random_position()
            if is_valid_position(x, z, existing_objects, 80):
                treasures.append({'x': x, 'z': z, 'type': 'diamond', 'collected': False})
                existing_objects.append({'x': x, 'z': z})
                valid_position = True
            attempts += 1

    # Keys
    for _ in range(NUM_KEYS):
        valid_position = False
        attempts = 0
        while not valid_position and attempts < 50:
            x, z = random_position()
            if is_valid_position(x, z, existing_objects, 80):
                keys.append({'x': x, 'z': z, 'collected': False})
                existing_objects.append({'x': x, 'z': z})
                valid_position = True
            attempts += 1

    # Hearts
    for _ in range(NUM_HEARTS):
        valid_position = False
        attempts = 0
        while not valid_position and attempts < 50:
            x, z = random_position()
            if is_valid_position(x, z, existing_objects, 80):
                hearts.append({'x': x, 'z': z, 'collected': False})
                existing_objects.append({'x': x, 'z': z})
                valid_position = True
            attempts += 1

    # Obstacles
    for _ in range(NUM_OBSTACLES):
        valid_position = False
        attempts = 0
        while not valid_position and attempts < 50:
            x, z = random_position(100)
            w = random.randint(40, 100)
            d = random.randint(40, 100)
            h = random.randint(80, 150)
            overlap = False
            for obj in existing_objects:
                if (abs(x - obj['x']) < (w/2 + 40) and 
                    abs(z - obj['z']) < (d/2 + 40)):
                    overlap = True
                    break
            if not overlap:
                obstacles.append((x, z, w, d, h))
                for dx in [-w/2, w/2]:
                    for dz in [-d/2, d/2]:
                        existing_objects.append({'x': x + dx, 'z': z + dz})
                valid_position = True
            attempts += 1

    # Enemies (spawn far from center)
    for _ in range(NUM_ENEMIES):
        valid_position = False
        attempts = 0
        while not valid_position and attempts < 50:
            x, z = random_position(150)
            if (is_valid_position(x, z, existing_objects, 60) and 
                distance(x, z, 0, 0) > 200):
                angle = random.uniform(0, 2*math.pi)
                dx, dz = math.cos(angle), math.sin(angle)
                speed = ENEMY_MIN_SPEED
                enemies.append({'x': x, 'z': z, 'dx': dx, 'dz': dz, 'speed': speed})
                existing_objects.append({'x': x, 'z': z})
                valid_position = True
            attempts += 1

# ---------- MAIN ----------
def main():
    global game_start_time
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Treasure Hunter Full Game")
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.1,0.1,0.2,1)
    glutDisplayFunc(display)
    glutKeyboardFunc(handle_movement)
    glutMouseFunc(mouse_click)
    glutIdleFunc(idle_func)
    glutReshapeFunc(reshape)
    game_start_time = time.time()
    init_game()
    glutMainLoop()
    

if __name__=="__main__":
    main()

