from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import math

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
GRID_LENGTH = 600
PLAYER_SPEED = 10
BULLET_SPEED = 25
ENEMY_SPEED = 1
fovY = 120
ASPECT_RATIO = WINDOW_WIDTH / WINDOW_HEIGHT

camera_mode = 0
camera_angle = 0
camera_height = 500
game_over = False

player_pos = [0.0, 0.0]
gun_angle = 0.0
life = 5
score = 0
missed_bullets = 0

cheat_mode = False
cheat_vision = False

enemies = []
ENEMY_COUNT = 5
bullets = []
player_dead_angle = 0

def init_enemies():
    global enemies
    enemies = []
    for _ in range(ENEMY_COUNT):
        ex = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)
        ey = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)
        enemies.append([ex, ey])
def is_enemy_in_line_of_sight(ex, ey, angle, threshold=3):
    dx = ex - player_pos[0]
    dy = ey - player_pos[1]
    target_angle = math.degrees(math.atan2(dy, dx))
    diff = (target_angle - angle) % 360
    if diff > 180:
        diff -= 360
    return abs(diff) < threshold

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_grid():
    square = 50
    glBegin(GL_QUADS)
    for x in range(-GRID_LENGTH, GRID_LENGTH, square):
        for y in range(-GRID_LENGTH, GRID_LENGTH, square):
            if ((x // square + y // square) % 2) == 0:
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.7, 0.5, 0.95)
            glVertex3f(x, y, 0)
            glVertex3f(x + square, y, 0)
            glVertex3f(x + square, y + square, 0)
            glVertex3f(x, y + square, 0)
    glEnd()

def distance2D(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2)

def draw_boundaries():
    wall_h = 100
    t = 10
    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(-GRID_LENGTH, 0, wall_h / 2)
    glScalef(t, 2 * GRID_LENGTH, wall_h)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0, 1, 1)
    glPushMatrix()
    glTranslatef(0, GRID_LENGTH, wall_h / 2)
    glScalef(2 * GRID_LENGTH, t, wall_h)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(0, 1, 0)
    glPushMatrix()
    glTranslatef(GRID_LENGTH, 0, wall_h / 2)
    glScalef(t, 2 * GRID_LENGTH, wall_h)
    glutSolidCube(1)
    glPopMatrix()
    glColor3f(1, 0, 1)
    glPushMatrix()
    glTranslatef(0, -GRID_LENGTH, wall_h / 2)
    glScalef(2 * GRID_LENGTH, t, wall_h)
    glutSolidCube(1)
    glPopMatrix()

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], 0)
    glRotatef(player_dead_angle, 0, 1, 0)
    glRotatef(gun_angle, 0, 0, 1)
    glPushMatrix()
    glColor3f(0.6, 0.6, 0.6)
    glScalef(30, 20, 50)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glColor3f(1, 1, 0)
    glTranslatef(0, 0, 35)
    glutSolidSphere(10, 20, 20)
    glPopMatrix()
    for side in (-1, 1):
        glPushMatrix()
        glColor3f(0, 1, 0)
        glTranslatef(20 * side, 0, 20)
        glRotatef(90, 0, 1, 0)
        gluCylinder(gluNewQuadric(), 5, 5, 30, 12, 3)
        glPopMatrix()
    for side in (-1, 1):
        glPushMatrix()
        glColor3f(0, 0, 1)
        glTranslatef(10 * side, 0, -25)
        glScalef(10, 10, 25)
        glutSolidCube(1)
        glPopMatrix()
    glPopMatrix()

def draw_enemies():
    for ex, ey in enemies:
        glPushMatrix()
        glTranslatef(ex, ey, 0)
        glColor3f(1, 0, 0)
        glutSolidSphere(20, 20, 20)
        glTranslatef(0, 0, 30)
        glColor3f(0, 0, 0)
        glutSolidSphere(10, 20, 20)
        glPopMatrix()

def draw_bullets():
    glColor3f(1, 0, 0)
    for bx, by, bz, _ in bullets:
        glPushMatrix()
        glTranslatef(bx, by, bz)
        glutSolidCube(5)
        glPopMatrix()


def update_bullets():
    global bullets, score, missed_bullets, game_over, enemies
    new_bullets = []
    for bx, by, bz, ang in bullets:
        nx = bx + BULLET_SPEED * math.cos(math.radians(ang))
        ny = by + BULLET_SPEED * math.sin(math.radians(ang))
        hit = None
        for e in enemies:
            if distance2D(nx, ny, e[0], e[1]) < 20:
                hit = e
                break

        if hit:
            enemies.remove(hit)
            score += 1
            ex = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)
            ey = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)
            enemies.append([ex, ey])
        else:
            if abs(nx) > GRID_LENGTH or abs(ny) > GRID_LENGTH:
                missed_bullets += 1
            else:
                new_bullets.append([nx, ny, bz, ang])

    bullets = new_bullets
    if missed_bullets >= 10:
        game_over = True
        player_dead_angle = 90


def update_enemies():
    global life, game_over, player_dead_angle, enemies
    for e in enemies[:]:
        dx = player_pos[0] - e[0]
        dy = player_pos[1] - e[1]
        dist = math.hypot(dx, dy)
        if dist < 30:
            life -= 1
            if life <= 0:
                game_over = True
                player_dead_angle = 90
            else:
                enemies.remove(e)
                ex = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)
                ey = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)
                enemies.append([ex, ey])
            return
        e[0] += ENEMY_SPEED * dx / dist
        e[1] += ENEMY_SPEED * dy / dist


def update_cheat_mode():
    global gun_angle, bullets
    ROTATION_SPEED = 3

    if cheat_mode:
        gun_angle += ROTATION_SPEED
        if gun_angle % 15 == 0:
            for ex, ey in enemies:
                if is_enemy_in_line_of_sight(ex, ey, gun_angle):
                    bullets.append([player_pos[0], player_pos[1], 20, gun_angle])


def restart_game():
    global life, score, missed_bullets, game_over, player_pos, gun_angle, player_dead_angle
    life = 5
    score = 0
    missed_bullets = 0
    game_over = False
    player_pos[:] = [0, 0]
    gun_angle = 0
    player_dead_angle = 0
    init_enemies()


def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, ASPECT_RATIO, 0.1, 3000)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if camera_mode == 0:
        radius = 600
        eyeX = radius * math.cos(math.radians(camera_angle))
        eyeY = radius * math.sin(math.radians(camera_angle))
        gluLookAt(eyeX, eyeY, camera_height, 0, 0, 0, 0, 0, 1)
    else:
        px, py = player_pos
        cosg = math.cos(math.radians(gun_angle))
        sing = math.sin(math.radians(gun_angle))
        if cheat_mode and cheat_vision:
            offset = 30
            cam_x = px + offset * cosg
            cam_y = py + offset * sing
            gluLookAt(cam_x, cam_y, 40, px + 300 * cosg, py + 300 * sing, 40, 0, 0, 1)
        else:
            eye_z = 60
            gluLookAt(px, py, eye_z, px + 100 * cosg, py + 100 * sing, eye_z, 0, 0, 1)

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setupCamera()
    draw_grid()
    draw_boundaries()
    draw_player()
    draw_enemies()
    draw_bullets()
    glDisable(GL_LIGHTING)
    draw_text(10, 730, f"Player Life Remaining: {life}")
    draw_text(10, 700, f"Game Score: {score}")
    draw_text(10, 670, f"Player Bullets Missed: {missed_bullets}")
    if game_over:
        draw_text(400, 400, "GAME OVER! Press R to restart")
    glutSwapBuffers()
def keyboardListener(key, x, y):
    global player_pos, gun_angle, cheat_mode, cheat_vision, camera_mode, game_over
    if key == b'w':
        player_pos[0] += PLAYER_SPEED * math.cos(math.radians(gun_angle))
        player_pos[1] += PLAYER_SPEED * math.sin(math.radians(gun_angle))
    elif key == b's':
        player_pos[0] -= PLAYER_SPEED * math.cos(math.radians(gun_angle))
        player_pos[1] -= PLAYER_SPEED * math.sin(math.radians(gun_angle))
    elif key == b'a':
        gun_angle += 5
    elif key == b'd':
        gun_angle -= 5
    elif key == b'c':
        cheat_mode = not cheat_mode
        if not cheat_mode:
            cheat_vision = False
    elif key == b'v' and cheat_mode:
        cheat_vision = not cheat_vision
    elif key == b'r' and game_over:
        restart_game()

def specialKeyListener(key, x, y):
    global camera_angle, camera_height
    if key == GLUT_KEY_UP:
        camera_height += 10
    elif key == GLUT_KEY_DOWN:
        camera_height -= 10
    elif key == GLUT_KEY_LEFT:
        camera_angle -= 5
    elif key == GLUT_KEY_RIGHT:
        camera_angle += 5

def mouseListener(button, state, x, y):
    global camera_mode
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not game_over:
        bullets.append([player_pos[0], player_pos[1], 20, gun_angle])
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera_mode = 1 - camera_mode

def idle():
    global gun_angle, player_dead_angle, game_over
    if not game_over:
        update_bullets()
        update_enemies()
        update_cheat_mode()
    else:
        if player_dead_angle < 90:
            player_dead_angle += 2
    glutPostRedisplay()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Bullet Frenzy 3D - Updated")
    glEnable(GL_DEPTH_TEST)
    init_enemies()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()

