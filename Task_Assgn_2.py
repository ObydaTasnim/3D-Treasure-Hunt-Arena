from OpenGL.GL import *
from OpenGL.GLUT import *
import random
import time
import sys

# ------------ GLOBALS ------------
win_w, win_h = 800, 600
catcher_w, catcher_h = 120, 20
catcher_x = win_w // 2 - catcher_w // 2
catcher_y = 50

diamond_size = 20
diamond_x = random.randint(100, win_w - 100)
diamond_y = win_h - 50
diamond_colors = [(1, 0.4, 1), (0.4, 1, 1), (0.6, 1, 0.9),(1.0, 0.6, 0.8), (0.6, 1.0, 0.2),(1.0, 1.0, 0.2)]
diamond_color = random.choice(diamond_colors)

score = 0
fall_speed = 80
paused = False
game_over = False
terminated = False  # NEW FLAG

prev_time = time.time()

# ------------ MIDPOINT LINE DRAWING ------------
def find_zone(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) >= abs(dy):
        if dx >= 0 and dy >= 0: return 0
        if dx < 0 and dy >= 0: return 3
        if dx < 0 and dy < 0: return 4
        return 7
    else:
        if dx >= 0 and dy >= 0: return 1
        if dx < 0 and dy >= 0: return 2
        if dx < 0 and dy < 0: return 5
        return 6

def to_zone0(x, y, zone):
    if zone == 0: return x, y
    if zone == 1: return y, x
    if zone == 2: return y, -x
    if zone == 3: return -x, y
    if zone == 4: return -x, -y
    if zone == 5: return -y, -x
    if zone == 6: return -y, x
    return x, -y

def from_zone0(x, y, zone):
    if zone == 0: return x, y
    if zone == 1: return y, x
    if zone == 2: return -y, x
    if zone == 3: return -x, y
    if zone == 4: return -x, -y
    if zone == 5: return -y, -x
    if zone == 6: return y, -x
    return x, -y

def draw_line(x1, y1, x2, y2):
    zone = find_zone(x1, y1, x2, y2)
    x1_z0, y1_z0 = to_zone0(x1, y1, zone)
    x2_z0, y2_z0 = to_zone0(x2, y2, zone)

    if x1_z0 > x2_z0:
        x1_z0, y1_z0, x2_z0, y2_z0 = x2_z0, y2_z0, x1_z0, y1_z0

    dx = x2_z0 - x1_z0
    dy = y2_z0 - y1_z0
    d = 2 * dy - dx
    incE = 2 * dy
    incNE = 2 * (dy - dx)

    x, y = x1_z0, y1_z0

    glBegin(GL_POINTS)
    while x <= x2_z0:
        x_draw, y_draw = from_zone0(x, y, zone)
        glVertex2f(x_draw, y_draw)
        if d > 0:
            y += 1
            d += incNE
        else:
            d += incE
        x += 1
    glEnd()

# ------------ OBJECT DRAWING ------------
def draw_diamond(x, y, s):
    h = s // 2
    glColor3f(*diamond_color)
    draw_line(x, y + h, x + h, y)
    draw_line(x + h, y, x, y - h)
    draw_line(x, y - h, x - h, y)
    draw_line(x - h, y, x, y + h)

def draw_catcher(x, y, w, h):
    glColor3f(1, 0, 0) if game_over else glColor3f(1, 1, 1)
    draw_line(x, y, x + 20, y + h)
    draw_line(x + 20, y + h, x + w - 20, y + h)
    draw_line(x + w - 20, y + h, x + w, y)
    draw_line(x, y, x + w, y)

def draw_text(x, y, text):
    glColor3f(1, 1, 1)
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))

# ------------ UPDATE GAME STATE ------------
def update():
    global diamond_y, diamond_x, diamond_color, score, fall_speed, game_over
    global prev_time

    if paused or game_over or terminated:
        return

    now = time.time()
    dt = now - prev_time
    prev_time = now

    diamond_y -= fall_speed * dt
    fall_speed += 0.5 * dt

    dx1 = diamond_x - diamond_size // 2
    dx2 = diamond_x + diamond_size // 2
    dy1 = diamond_y - diamond_size // 2
    dy2 = diamond_y + diamond_size // 2

    cx1, cx2 = catcher_x, catcher_x + catcher_w
    cy1, cy2 = catcher_y, catcher_y + catcher_h

    if dx1 < cx2 and dx2 > cx1 and dy1 < cy2 and dy2 > cy1:
        score += 1
        print("Score:", score)
        diamond_x = random.randint(100, win_w - 100)
        diamond_y = win_h - 50
        diamond_color = random.choice(diamond_colors)
        fall_speed += 5
    elif diamond_y + diamond_size // 2 < 0:
        print("Game Over! Final Score:", score)
        game_over = True

# ------------ BUTTONS ------------
def draw_buttons():
    glColor3f(0, 1, 1)
    draw_line(40, 560, 60, 580)
    draw_line(40, 560, 60, 540)
    draw_line(60, 540, 60, 580)

    glColor3f(1, 0.6, 0)
    if paused:
        draw_line(130, 540, 150, 560)
        draw_line(150, 560, 130, 580)
        draw_line(130, 580, 130, 540)
    else:
        draw_line(130, 540, 135, 580)
        draw_line(145, 540, 150, 580)

    glColor3f(1, 0, 0)
    draw_line(220, 540, 240, 580)
    draw_line(220, 580, 240, 540)

# ------------ INPUT HANDLING ------------
def key_handler(key, x, y):
    global catcher_x
    if paused or game_over or terminated: return
    if key == b'a' and catcher_x > 0:
        catcher_x -= 20
    elif key == b'd' and catcher_x + catcher_w < win_w:
        catcher_x += 20

def special_handler(key, x, y):
    global catcher_x
    if paused or game_over or terminated: return
    if key == GLUT_KEY_LEFT and catcher_x > 0:
        catcher_x -= 20
    elif key == GLUT_KEY_RIGHT and catcher_x + catcher_w < win_w:
        catcher_x += 20

def mouse_handler(button, state, x, y):
    global paused, game_over, diamond_x, diamond_y, diamond_color
    global catcher_x, score, fall_speed, terminated

    if state != GLUT_DOWN or terminated:
        return

    mx, my = x, win_h - y
    if 40 <= mx <= 60 and 540 <= my <= 580:
        diamond_x = random.randint(100, win_w - 100)
        diamond_y = win_h - 50
        diamond_color = random.choice(diamond_colors)
        catcher_x = win_w // 2 - catcher_w // 2
        score = 0
        fall_speed = 80
        paused = False
        game_over = False
        terminated = False
        print("Starting Over")
    elif 130 <= mx <= 150 and 540 <= my <= 580:
        paused = not paused
    elif 220 <= mx <= 240 and 540 <= my <= 580:
        print(f"Goodbye! Final Score: {score}")
        terminated = True  # freeze the game
        # sys.exit(0) <-- only use if you want window to force close

# ------------ RENDERING ------------
def display():
    glClearColor(0, 0, 0, 1)
    glClear(GL_COLOR_BUFFER_BIT)

    if terminated:
        draw_text(win_w // 2 - 90, win_h // 2, f"Goodbye! Final Score: {score}")
    else:
        draw_buttons()
        draw_diamond(diamond_x, int(diamond_y), diamond_size)
        draw_catcher(catcher_x, catcher_y, catcher_w, catcher_h)

    glutSwapBuffers()

def idle():
    update()
    glutPostRedisplay()

# ------------ MAIN ------------
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(win_w, win_h)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Catch the Diamonds!")
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, win_w, 0, win_h, -1, 1)

    glutDisplayFunc(display)
    glutKeyboardFunc(key_handler)
    glutSpecialFunc(special_handler)
    glutMouseFunc(mouse_handler)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()

