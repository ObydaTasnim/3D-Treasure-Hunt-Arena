from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import random
import math
import time
import sys
from PIL import Image

# Window and arena parameters
WIN_W, WIN_H = 1000, 800
GRID_SIZE = 600
WALL_HEIGHT = 80
WALL_THICKNESS = 20

# Player parameters
PLAYER_RADIUS = 30
PLAYER_SPEED = 8
ROT_SPEED = 4
px, pz = 0.0, 0.0
p_angle = 0.0
p_color = (0.2, 0.6, 0.9)

# Camera position
cam_x, cam_y, cam_z = 0, 500, 800

# Gameplay variables
lives = 3
max_lives = 10
score = 0
keys_collected = 0
game_paused = False
cheat_mode = False

# Game object constants
NUM_TREASURES = 8
NUM_KEYS = 5
NUM_HEARTS = 3
KEY_RADIUS = 8
NUM_DIAMONDS = 5  # Always keep 5 diamonds on screen

# Treasure types
TREASURE_TYPES = {
    'gold': {'points': 10, 'size': 40, 'color': (1.0, 0.5, 0.0)},
    'silver': {'points': 10, 'size': 30, 'color': (0.75, 0.75, 0.75)},
    'diamond': {'points': 25, 'size': 50, 'color': (0.0, 0.8, 0.8)},  
}


NUM_ENEMIES = 5
ENEMY_RADIUS = 25
ENEMY_INITIAL_SPEED = 1.5  # Start slower

# Global containers
keys = []
treasures = []
enemies = []
hearts = []
traps = [(-200, 200), (150, -150), (250, 250), (-300, -100), (300, -300)]

# Timers
start_time = None
diamond_regeneration_time = 0
message_display_time = 0
current_message = ""
frozen_until = 0  # Time when player unfreezes

# Animation variables
key_bounce_phase = 0
diamond_spin_angle = 0
diamond_bounce_phase = 0
treasure_open_angle = {}  # Track opening animation for each treasure

# Button parameters
BUTTON_SIZE = 40
BUTTON_MARGIN = 10
buttons = {
    'restart': (WIN_W - 3*(BUTTON_SIZE + BUTTON_MARGIN), WIN_H - BUTTON_SIZE - BUTTON_MARGIN,
                BUTTON_SIZE, BUTTON_SIZE),
    'pause': (WIN_W - 2*(BUTTON_SIZE + BUTTON_MARGIN), WIN_H - BUTTON_SIZE - BUTTON_MARGIN,
              BUTTON_SIZE, BUTTON_SIZE),
    'exit': (WIN_W - (BUTTON_SIZE + BUTTON_MARGIN), WIN_H - BUTTON_SIZE - BUTTON_MARGIN,
             BUTTON_SIZE, BUTTON_SIZE),
}

# Brick texture
brick_texture_id = None

def random_position(margin=150):
    return (
        random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin),
        random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
    )

def load_texture(path):
    img = Image.open(path)
    img = img.convert("RGB")
    img_data = img.tobytes()
    w, h = img.size
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, img_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    return tex_id

def init_game():
    global keys, treasures, enemies, hearts, lives, score, keys_collected
    global px, pz, p_angle, game_paused, cheat_mode, start_time, diamond_regeneration_time
    global treasure_open_angle, message_display_time, current_message, frozen_until

    lives = 3
    score = 0
    keys_collected = 0
    px, pz = 0.0, 0.0
    p_angle = 0.0
    game_paused = False
    cheat_mode = False
    diamond_regeneration_time = time.time()
    message_display_time = 0
    current_message = ""
    frozen_until = 0
    treasure_open_angle = {}

    treasures.clear()
    # Create regular treasure boxes (gold and silver)
    ttypes = ['gold', 'silver'] * 4  # 8 treasure boxes (4 gold, 4 silver)
    for _ in range(NUM_TREASURES):
        x, z = random_position()
        ttype = ttypes.pop(0) if ttypes else random.choice(['gold', 'silver'])
        treasures.append({'x': x, 'z': z, 'type': ttype, 'opened': False, 'key_required': True})
        treasure_open_angle[len(treasures)-1] = 0  # Initialize opening angle
    
    # Add diamonds (always 5 on screen)
    for _ in range(NUM_DIAMONDS):
        x, z = random_position()
        treasures.append({'x': x, 'z': z, 'type': 'diamond', 'opened': False, 'key_required': False})
        treasure_open_angle[len(treasures)-1] = 0

    keys.clear()
    for _ in range(NUM_KEYS):
        x, z = random_position()
        keys.append({'x': x, 'z': z, 'collected': False})

    hearts.clear()
    for _ in range(NUM_HEARTS):
        x, z = random_position()
        hearts.append({'x': x, 'z': z, 'collected': False})

    enemies.clear()
    for _ in range(NUM_ENEMIES):
        margin = 200
        x1 = random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
        z1 = random.uniform(-GRID_SIZE + margin, GRID_SIZE - margin)
        size = random.uniform(120, 200)
        x2 = x1 + size
        z2 = z1 + size
        path = [(x1, z1), (x2, z1), (x2, z2), (x1, z2)]
        enemies.append({
            'path': path,
            'pos': [path[0][0], path[0][1]],
            'speed': ENEMY_INITIAL_SPEED,
            'dir_index': 0,
        })

    start_time = time.time()

def distance(x1, z1, x2, z2):
    return math.hypot(x1 - x2, z1 - z2)

def draw_rect(x, y, w, h):
    glBegin(GL_LINE_LOOP)
    glVertex2i(x, y)
    glVertex2i(x + w, y)
    glVertex2i(x + w, y + h)
    glVertex2i(x, y + h)
    glEnd()

def draw_button(x, y, w, h, color, label, paused_state=False):
    glColor3f(*color)
    draw_rect(x, y, w, h)
    cx = x + w//2
    cy = y + h//2
    if label == 'restart':
        glBegin(GL_LINES)
        glVertex2i(cx + 10, cy + 12)
        glVertex2i(cx - 8, cy)
        glVertex2i(cx - 8, cy)
        glVertex2i(cx + 10, cy - 12)
        glEnd()
    elif label == 'pause':
        bar_color = (0.0, 0.7, 0.0) if not paused_state else (0.4, 0.4, 0.4)
        glColor3f(*bar_color)
        glBegin(GL_QUADS)
        glVertex2i(cx - 8, cy + 12); glVertex2i(cx - 4, cy + 12)
        glVertex2i(cx - 4, cy - 12); glVertex2i(cx - 8, cy - 12)
        glVertex2i(cx + 4, cy + 12); glVertex2i(cx + 8, cy + 12)
        glVertex2i(cx + 8, cy - 12); glVertex2i(cx + 4, cy - 12)
        glEnd()
    elif label == 'exit':
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2i(cx - 12, cy - 12); glVertex2i(cx + 12, cy + 12)
        glVertex2i(cx + 12, cy - 12); glVertex2i(cx - 12, cy + 12)
        glEnd()

def draw_grid():
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_LINES)
    for i in range(-GRID_SIZE, GRID_SIZE + 1, 40):
        glVertex3f(i, -GRID_SIZE, 0); glVertex3f(i, GRID_SIZE, 0)
        glVertex3f(-GRID_SIZE, i, 0); glVertex3f(GRID_SIZE, i, 0)
    glEnd()

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(70, WIN_W / WIN_H, 0.1, 2000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(cam_x, cam_y, cam_z, 0, 0, 0, 0, 0, 1)

def draw_walls():
    def draw_brick_wall(x, y, z, width, height, wall_height, brick_width=40, brick_height=20):
        glPushMatrix()
        glTranslatef(x, y, z)

        rows = int(wall_height / brick_height)
        cols = int(width / brick_width)
        for row in range(rows):
            offset = (brick_width // 2) if row % 2 == 1 else 0  # Staggered rows
            for col in range(cols):
                bx = col * brick_width - width / 2 + offset
                by = row * brick_height - height / 2
                glColor3f(0.7, 0.2, 0.1)  # Brick color
                glBegin(GL_QUADS)
                glVertex3f(bx, by, 0)
                glVertex3f(bx + brick_width, by, 0)
                glVertex3f(bx + brick_width, by + brick_height, 0)
                glVertex3f(bx, by + brick_height, 0)
                glEnd()

                # Brick outline
                glColor3f(0.1, 0.1, 0.1)
                glBegin(GL_LINE_LOOP)
                glVertex3f(bx, by, 0)
                glVertex3f(bx + brick_width, by, 0)
                glVertex3f(bx + brick_width, by + brick_height, 0)
                glVertex3f(bx, by + brick_height, 0)
                glEnd()
        glPopMatrix()

    # Front wall (top)
    draw_brick_wall(0, GRID_SIZE + WALL_THICKNESS / 2, WALL_HEIGHT / 2,
                    GRID_SIZE * 2 + WALL_THICKNESS, WALL_THICKNESS, WALL_HEIGHT)

    # Back wall (bottom)
    draw_brick_wall(0, -GRID_SIZE - WALL_THICKNESS / 2, WALL_HEIGHT / 2,
                    GRID_SIZE * 2 + WALL_THICKNESS, WALL_THICKNESS, WALL_HEIGHT)

    # Left wall
    glPushMatrix()
    glRotatef(90, 0, 0, 1)
    draw_brick_wall(0, -GRID_SIZE - WALL_THICKNESS / 2, WALL_HEIGHT / 2,
                    GRID_SIZE * 2 + WALL_THICKNESS, WALL_THICKNESS, WALL_HEIGHT)
    glPopMatrix()

    # Right wall
    glPushMatrix()
    glRotatef(90, 0, 0, 1)
    draw_brick_wall(0, GRID_SIZE + WALL_THICKNESS / 2, WALL_HEIGHT / 2,
                    GRID_SIZE * 2 + WALL_THICKNESS, WALL_THICKNESS, WALL_HEIGHT)
    glPopMatrix()

def draw_human_character():
    glPushMatrix()
    glTranslatef(px, pz, 0)
    glRotatef(p_angle, 0, 0, 1)
    
    # Body
    glPushMatrix()
    glTranslatef(0, 0, PLAYER_RADIUS)
    glColor3f(0.2, 0.6, 0.9)
    glScalef(PLAYER_RADIUS*0.8, PLAYER_RADIUS*0.4, PLAYER_RADIUS*1.2)
    glutSolidCube(1)
    glPopMatrix()
    
    # Head
    glPushMatrix()
    glTranslatef(0, 0, PLAYER_RADIUS*2.0)
    glColor3f(0.9, 0.7, 0.5)
    glutSolidSphere(PLAYER_RADIUS*0.5, 15, 15)
    glPopMatrix()
    
    # Arms
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side*PLAYER_RADIUS*0.7, 0, PLAYER_RADIUS*1.2)
        glColor3f(0.9, 0.7, 0.5)
        glScalef(PLAYER_RADIUS*0.3, PLAYER_RADIUS*0.2, PLAYER_RADIUS*0.8)
        glutSolidCube(1)
        glPopMatrix()
    
    # Legs
    for side in [-1, 1]:
        glPushMatrix()
        glTranslatef(side*PLAYER_RADIUS*0.3, 0, PLAYER_RADIUS*0.4)
        glColor3f(0.3, 0.2, 0.1)
        glScalef(PLAYER_RADIUS*0.3, PLAYER_RADIUS*0.2, PLAYER_RADIUS*0.8)
        glutSolidCube(1)
        glPopMatrix()
    
    glPopMatrix()

def draw_key_shape():
    # Simplified key shape - just a circle and a rectangle
    glPushMatrix()
    # Key head (circle)
    glutSolidSphere(8, 10, 10)
    
    # Key shaft
    glTranslatef(15, 0, 0)
    glScalef(20, 3, 3)
    glutSolidCube(1)
    glPopMatrix()

def draw_keys():
    global key_bounce_phase
    for key in keys:
        if not key['collected'] or cheat_mode:
            glPushMatrix()
            bounce = math.sin(key_bounce_phase) * 10  # Reduced bounce height
            glTranslatef(key['x'], key['z'], KEY_RADIUS + bounce + 5)
            glColor3f(1.0, 0.9, 0.0)
            draw_key_shape()
            glPopMatrix()

def draw_diamond_shape():
    glBegin(GL_TRIANGLES)
    vertices = [
        (0, 0, 0.5), (0.5, 0.5, 0), (-0.5, 0.5, 0),
        (-0.5, -0.5, 0), (0.5, -0.5, 0), (0, 0, -0.5)
    ]
    faces = [
        (0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1),
        (5, 2, 1), (5, 3, 2), (5, 4, 3), (5, 1, 4)
    ]
    for face in faces:
        for idx in face:
            glVertex3f(*vertices[idx])
    glEnd()

def draw_treasure_box(idx, size, color, opened=False, open_angle=0):
    glPushMatrix()
    glColor3f(*color)
    
    if opened:
        # Draw the base of the box
        glPushMatrix()
        glTranslatef(0, 0, size/4)
        glScalef(size, size, size/2)
        glutSolidCube(1)
        glPopMatrix()
        
        # Draw the lid at an angle
        glPushMatrix()
        glTranslatef(0, -size/2, size/2)
        glRotatef(open_angle, 1, 0, 0)
        glTranslatef(0, size/2, -size/4)
        glScalef(size, size/10, size/2)
        glutSolidCube(1)
        glPopMatrix()
    else:
        # Draw closed box
        glScalef(size, size, size/2)
        glutSolidCube(1)
        
        # Draw lid
        glPushMatrix()
        glTranslatef(0, 0, 0.5)
        glScalef(1.02, 1.02, 0.1)
        glutSolidCube(1)
        glPopMatrix()
    
    glPopMatrix()

def draw_treasures():
    global diamond_spin_angle, diamond_bounce_phase
    for i, tr in enumerate(treasures):
        props = TREASURE_TYPES[tr['type']]
        size, color = props['size'], props['color']
        glPushMatrix()
        glTranslatef(tr['x'], tr['z'], size/2)
        
        if tr['type'] == 'diamond': 
            if not tr['opened'] or cheat_mode:
                bounce = math.sin(diamond_bounce_phase) * 20
                glTranslatef(0, 0, bounce)
                glRotatef(diamond_spin_angle, 0, 0, 1)
                glRotatef(diamond_spin_angle * 0.7, 1, 0, 0)
                glColor3f(0.0, 0.8, 0.8)  # Turquoise color for diamonds
                glScalef(size, size, size)
                draw_diamond_shape()
        else:
            # Draw treasure box with opening animation if applicable
            open_angle = treasure_open_angle.get(i, 0)
            draw_treasure_box(i, size, color, tr['opened'], open_angle)
        
        glPopMatrix()

def draw_hearts():
    for heart in hearts:
        if not heart['collected']:
            glPushMatrix()
            glTranslatef(heart['x'], heart['z'], 20)
            glColor3f(0.3, 0.0, 0.0)
            glutSolidSphere(12, 15, 15)
            glPopMatrix()

def draw_enemies():
    for enemy in enemies:
        glPushMatrix()
        glTranslatef(enemy['pos'][0], enemy['pos'][1], ENEMY_RADIUS)
        glColor3f(0.8, 0.0, 0.0)
        glutSolidSphere(ENEMY_RADIUS, 20, 20)
        glPopMatrix()

def draw_traps():
    glColor3f(0.6, 0.0, 0.0)
    for tx, tz in traps:
        glPushMatrix()
        glTranslatef(tx, tz, 0)
        for i in range(3):
            glPushMatrix()
            glRotatef(i * 120, 0, 0, 1)
            glTranslatef(15, 0, 25)
            glRotatef(-90, 1, 0, 0)
            glutSolidCone(8, 50, 8, 8)
            glPopMatrix()
        glPopMatrix()

def draw_hud():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 1)

    current_time = int(time.time() - start_time) if start_time else 0
    hud_text = (f"Lives: {lives}/{max_lives}    Keys: {keys_collected}/{NUM_KEYS}    "
                f"Score: {score}    Time: {current_time}s    {'[PAUSED]' if game_paused else ''} {'[CHEAT]' if cheat_mode else ''}")
    glRasterPos2f(20, WIN_H - 40)
    for ch in hud_text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    for i in range(lives):
        glPushMatrix()
        glTranslatef(20 + i*25, WIN_H - 80, 0)
        glColor3f(1.0, 0.0, 0.0)
        glutSolidSphere(8, 10, 10)
        glPopMatrix()


    if current_message and time.time() - message_display_time < 3:
        glRasterPos2f(WIN_W//2 - len(current_message)*4, WIN_H - 80)
        for ch in current_message:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    
    if time.time() < frozen_until:
        frozen_text = f"FROZEN! {int(frozen_until - time.time())}s"
        glRasterPos2f(WIN_W//2 - 50, WIN_H - 120)
        for ch in frozen_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

    draw_button(*buttons['restart'], (0.0, 0.7, 0.7), 'restart')
    draw_button(*buttons['pause'], (0.0, 0.7, 0.0), 'pause', paused_state=game_paused)
    draw_button(*buttons['exit'], (1.0, 0.0, 0.0), 'exit')

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_animations():
    global key_bounce_phase, diamond_spin_angle, diamond_bounce_phase
    
    key_bounce_phase += 0.1
    diamond_spin_angle = (diamond_spin_angle + 2) % 360
    diamond_bounce_phase += 0.12
    
    
    for i in treasure_open_angle:
        if treasures[i]['opened'] and treasure_open_angle[i] < 135:
            treasure_open_angle[i] += 5

def update_enemies():
    for enemy in enemies:
        enemy['speed'] = ENEMY_INITIAL_SPEED/2 + score * 0.1
        path = enemy['path']
        tgt = path[enemy['dir_index']]
        dx, dz = tgt[0] - enemy['pos'][0], tgt[1] - enemy['pos'][1]
        dist = math.hypot(dx, dz)
        if dist < 10:
            enemy['dir_index'] = (enemy['dir_index'] + 1) % len(path)
        elif dist > 0:
            enemy['pos'][0] += dx/dist * enemy['speed']
            enemy['pos'][1] += dz/dist * enemy['speed']
        if abs(enemy['pos'][0]) > GRID_SIZE or abs(enemy['pos'][1]) > GRID_SIZE:
            enemy['pos'][0], enemy['pos'][1] = random_position(margin=100)

def regenerate_diamonds():
    global diamond_regeneration_time
    current_time = time.time()
    
    
    if current_time - diamond_regeneration_time >= 3: 
        diamond_regeneration_time = current_time
        
        # Find all diamonds and regenerate them
        for tr in treasures:
            if tr['type'] == 'diamond' and tr['opened']:
                tr['opened'] = False
                tr['x'], tr['z'] = random_position()
                treasure_open_angle[treasures.index(tr)] = 0

def check_collisions():
    global lives, score, keys_collected, px, pz, current_message, message_display_time, frozen_until
    
    
    for key in keys:
        if not key['collected'] and distance(px, pz, key['x'], key['z']) < PLAYER_RADIUS + KEY_RADIUS:
            key['collected'] = True
            keys_collected += 1
            score += 5
            current_message = "Key Found!"
            message_display_time = time.time()

    
    for i, tr in enumerate(treasures):
        if not tr['opened'] and tr['type'] != 'diamond' and tr['key_required']:
            props = TREASURE_TYPES[tr['type']]
            if distance(px, pz, tr['x'], tr['z']) < PLAYER_RADIUS + props['size']/2:
                if keys_collected > 0:
                    tr['opened'] = True
                    tr['key_required'] = False
                    keys_collected -= 1
                    score += props['points']
                    current_message = f"Box Opened. {props['points']} points!"
                    message_display_time = time.time()
                else:
                    current_message = "You need a key to open this box!"
                    message_display_time = time.time()
        
        # Check diamond collision
        elif not tr['opened'] and tr['type'] == 'diamond':
            props = TREASURE_TYPES[tr['type']]
            if distance(px, pz, tr['x'], tr['z']) < PLAYER_RADIUS + props['size']/2:
                tr['opened'] = True
                score += props['points']
                current_message = f"Diamond Collected! {props['points']} points!"
                message_display_time = time.time()
                
                # Generate a new diamond to replace the collected one
                x, z = random_position()
                treasures.append({'x': x, 'z': z, 'type': 'diamond', 'opened': False, 'key_required': False})
                treasure_open_angle[len(treasures)-1] = 0

    
    for heart in hearts:
        if not heart['collected'] and distance(px, pz, heart['x'], heart['z']) < PLAYER_RADIUS + 15:
            heart['collected'] = True
            if lives < max_lives:
                lives += 1
            score += 10
            current_message = "Extra Life!"
            message_display_time = time.time()

    # enemy collisions
    for enemy in enemies:
        if distance(px, pz, enemy['pos'][0], enemy['pos'][1]) < PLAYER_RADIUS + ENEMY_RADIUS:
            lives = max(0, lives - 1)  # Prevent lives from going below zero
            enemy['pos'][0], enemy['pos'][1] = random_position(margin=100)
            current_message = "Enemy Hit!"
            message_display_time = time.time()
            break

    # Check trap collisions
    for tx, tz in traps:
        if distance(px, pz, tx, tz) < PLAYER_RADIUS + 25:
            lives = max(0, lives - 1)  # Prevent lives from going below zero
            dx, dz = px - tx, pz - tz
            L = math.hypot(dx, dz)
            if L > 0:
                px += dx/L * 60
                pz += dz/L * 60
            current_message = "Trap Activated! Frozen for 5 seconds!"
            message_display_time = time.time()
            frozen_until = time.time() + 5  # Freeze player for 5 seconds
            break

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glEnable(GL_DEPTH_TEST)
    setup_camera()

    if not game_paused and time.time() >= frozen_until:  # Only update if not frozen
        update_animations()
        update_enemies()
        check_collisions()
        regenerate_diamonds()

    draw_grid()
    draw_walls()
    draw_keys()
    draw_treasures()
    draw_hearts()
    draw_enemies()
    draw_traps()
    draw_human_character()
    draw_hud()

    if all(tr['opened'] for tr in treasures if tr['type'] != 'diamond') and keys_collected >= 0:
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIN_W, 0, WIN_H)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glColor3f(0, 1, 0)
        win_text = f"VICTORY! Final Score: {score}"
        glRasterPos2f(WIN_W//2 - 100, WIN_H//2)
        for ch in win_text: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

    if lives <= 0:
        glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0, WIN_W, 0, WIN_H)
        glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
        glColor3f(1, 0, 0)
        over_text = f"GAME OVER! Final Score: {score}"
        glRasterPos2f(WIN_W//2 - 120, WIN_H//2)
        for ch in over_text: glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

    glutSwapBuffers()

def handle_movement(key, x, y):
    global px, pz, game_paused, cheat_mode
    if game_paused and key != b' ':
        return
    
    # Don't allow movement if player is frozen
    if time.time() < frozen_until:
        return

    if key in [b'w', b'W']:  # forward (up in z-axis)
        nz = pz + PLAYER_SPEED
        if abs(px) < GRID_SIZE - PLAYER_RADIUS and abs(nz) < GRID_SIZE - PLAYER_RADIUS:
            pz = nz
    elif key in [b'z', b'Z']:  # backward (down in z-axis) - changed from S to Z
        nz = pz - PLAYER_SPEED
        if abs(px) < GRID_SIZE - PLAYER_RADIUS and abs(nz) < GRID_SIZE - PLAYER_RADIUS:
            pz = nz
    elif key in [b'a', b'A']:  # left (negative x-axis)
        nx = px - PLAYER_SPEED
        if abs(nx) < GRID_SIZE - PLAYER_RADIUS and abs(pz) < GRID_SIZE - PLAYER_RADIUS:
            px = nx
    elif key in [b's', b'S']:  # right (positive x-axis) - changed from D to S
        nx = px + PLAYER_SPEED
        if abs(nx) < GRID_SIZE - PLAYER_RADIUS and abs(pz) < GRID_SIZE - PLAYER_RADIUS:
            px = nx
    elif key in [b'r', b'R']:
        init_game()
    elif key == b' ':
        game_paused = not game_paused
    elif key in [b'c', b'C']:
        cheat_mode = not cheat_mode
    elif key == b'\x1b':
        sys.exit()

def handle_mouse(button, state, x, y):
    global game_paused
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        my = WIN_H - y
        rx, ry, rw, rh = buttons['restart']
        if rx <= x <= rx + rw and ry <= my <= ry + rh:
            init_game()
        px_, py_, pw, ph = buttons['pause']
        if px_ <= x <= px_ + pw and py_ <= my <= py_ + ph:
            game_paused = not game_paused
        ex, ey, ew, eh = buttons['exit']
        if ex <= x <= ex + ew and ey <= my <= ey + eh:
            glutDestroyWindow(window_id)
            sys.exit()

def timer(value):
    if not game_paused:
        glutPostRedisplay()
    glutTimerFunc(16, timer, 0)

def reshape(width, height):
    global WIN_W, WIN_H
    WIN_W, WIN_H = width, height
    glViewport(0, 0, width, height)

def main():
    global window_id, brick_texture_id
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    window_id = glutCreateWindow(b"Enhanced 3D Treasure Hunter")

    glEnable(GL_DEPTH_TEST)
    glClearColor(0.1, 0.1, 0.2, 1.0)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION, [100, 100, 200, 1])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1])
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    glutDisplayFunc(display)
    glutKeyboardFunc(handle_movement)
    glutMouseFunc(handle_mouse)
    glutReshapeFunc(reshape)
    glutTimerFunc(0, timer, 0)

    init_game()

    print("=== ENHANCED 3D TREASURE HUNTER ===")
    print("Controls: WASD to move/rotate, R restart, SPACE pause, C cheat toggle, ESC exit. Click buttons with the mouse.")
    glutMainLoop()

if __name__ == "__main__":
    main()
