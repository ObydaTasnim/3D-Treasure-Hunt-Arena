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
fovY = 120 #Field of View
ASPECT_RATIO = WINDOW_WIDTH / WINDOW_HEIGHT

camera_mode = 0
camera_angle = 0
camera_height = 500
game_over = False

player_pos = [0.0, 0.0]
gun_angle = 0.0
player_angle = 0.0           # <-- new: player's facing angle for movement
life = 5
score = 0
missed_bullets = 0

cheat_mode = False
cheat_vision = False

enemies = []
ENEMY_COUNT = 5
bullets = []
player_dead_angle = 0

# Enemy breathing phase
enemy_breathe_phase = 0

# Camera anchor storage for cheat vision
cheat_cam_anchor_pos = None
cheat_cam_anchor_target = None


def init_enemies():  #new random positions for all enemies, used on start or reset
    global enemies
    enemies = []
    for _ in range(ENEMY_COUNT):
        ex = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)    #50-unit margin from the boundaries,preventing enemies clash with wall
        ey = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)
        enemies.append([ex, ey])


def is_enemy_in_line_of_sight(ex, ey, angle, threshold=3): #used by cheat mode to decide whether to fire automatically.
    dx = ex - player_pos[0]
    dy = ey - player_pos[1]
    target_angle = math.degrees(math.atan2(dy, dx)) #the angle of the vector from the x-axis
    diff = (target_angle - angle) % 360
    if diff > 180:
        diff -= 360
    return abs(diff) < threshold


def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18): #given template
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


def draw_grid():       # a chess board-style floor made of quads
    square = 50
    glBegin(GL_QUADS)
    for x in range(-GRID_LENGTH, GRID_LENGTH, square): #left right
        for y in range(-GRID_LENGTH, GRID_LENGTH, square): #top bottom
            if ((x // square + y // square) % 2) == 0: #If even, choose white; else purple-ish
                glColor3f(1.0, 1.0, 1.0)
            else:
                glColor3f(0.7, 0.5, 0.95)
            glVertex3f(x, y, 0)
            glVertex3f(x + square, y, 0)
            glVertex3f(x + square, y + square, 0)
            glVertex3f(x, y + square, 0)
    glEnd()


def distance2D(x1, y1, x2, y2):
    return math.hypot(x1 - x2, y1 - y2) #returns Euclidean distance


def draw_boundaries():
    wall_h = 100
    t = 10
    glColor3f(0, 0, 1)
    glPushMatrix()
    glTranslatef(-GRID_LENGTH, 0, wall_h / 2) #center of cube to wall center
    glScalef(t, 2 * GRID_LENGTH, wall_h) #stretch unit cube to rectangular
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

    # DEATH 
    if game_over:
        # Rotating the body around X to lie down (animated by player_dead_angle)
        glPushMatrix()
        glRotatef(player_dead_angle, 1, 0, 0)

        # Torso (cuboid)
        glPushMatrix()
        glColor3f(0.3, 0.3, 1.0)
        glScalef(20, 15, 40)
        glutSolidCube(1)
        glPopMatrix()

        # Head (sphere) placed relative to torso (still affected by the lie-down rotation)
        glPushMatrix()
        glColor3f(1.0, 0.9, 0.6)
        glTranslatef(0, 0, 30)
        glutSolidSphere(10, 20, 20)
        glPopMatrix()

        # Legs (two cuboid legs)
        for side in (-1, 1):
            glPushMatrix()
            glColor3f(0.0, 0.0, 0.7)
            glTranslatef(7 * side, 0, -20)
            glScalef(7, 7, 20)
            glutSolidCube(1)
            glPopMatrix()

        glPopMatrix()  # end body-lying-block

        #  the gun separately so it remains vertical
        glPushMatrix()
        glColor3f(0.1, 0.8, 0.1)
        # placing the gun base a bit above the ground/torso center 
        glTranslatef(0, 0, 30)
        # gluCylinder's default axis is +Z, so no extra rotation needed to make it point up
        gluCylinder(gluNewQuadric(), 3, 3, 30, 12, 3)
        glPopMatrix()

    # ALIVE: normal pose (gun points according to gun_angle) 
    else:
        # small rotation variable is kept for compatibility with falling animation logic
        glRotatef(player_dead_angle, 0, 1, 0)
        glRotatef(gun_angle, 0, 0, 1)

        # Torso (cuboid)
        glPushMatrix()
        glColor3f(0.3, 0.3, 1.0)
        glScalef(20, 15, 40)
        glutSolidCube(1)
        glPopMatrix()

        # Head (sphere)
        glPushMatrix()
        glColor3f(1.0, 0.9, 0.6)
        glTranslatef(0, 0, 30)
        glutSolidSphere(10, 20, 20)
        glPopMatrix()

        # Gun aligned with gun_angle in XY plane (same behavior as before)
        glPushMatrix()
        glColor3f(0.1, 0.8, 0.1)
        glTranslatef(0, 0, 15)
        glRotatef(90, 0, 1, 0)  # making the cylinder point along the X axis, then gun_angle rotates it
        gluCylinder(gluNewQuadric(), 3, 3, 30, 12, 3)
        glPopMatrix()

        # Legs (two cuboid legs)
        for side in (-1, 1):
            glPushMatrix()
            glColor3f(0.0, 0.0, 0.7)
            glTranslatef(7 * side, 0, -20)
            glScalef(7, 7, 20)
            glutSolidCube(1)
            glPopMatrix()

    glPopMatrix()




def draw_enemies():
    global enemy_breathe_phase
    enemy_breathe_phase += 0.05
    scale = 1 + 0.2 * math.sin(enemy_breathe_phase)  # breathing

    for ex, ey in enemies:
        glPushMatrix()
        glTranslatef(ex, ey, 0)
        glScalef(scale, scale, scale)  # apply breathing
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
    global bullets, score, missed_bullets, game_over, enemies, player_dead_angle
    new_bullets = []
    for bx, by, bz, ang in bullets:
        nx = bx + BULLET_SPEED * math.cos(math.radians(ang))
        ny = by + BULLET_SPEED * math.sin(math.radians(ang))
        hit = None
        for e in enemies:
            if distance2D(nx, ny, e[0], e[1]) < 20: #If distance < 20 then bullet is close enough to count as a hit
                hit = e # tops after first hit to avoid double-counting.
                break

        if hit:
            enemies.remove(hit) 
            score += 1
            ex = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50) #Respawn enemy at a new random position
            ey = random.randint(-GRID_LENGTH + 50, GRID_LENGTH - 50)
            enemies.append([ex, ey])
        else:
            if abs(nx) > GRID_LENGTH or abs(ny) > GRID_LENGTH: #bullet position lies outside the grid bounds
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

m
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
    global life, score, missed_bullets, game_over, player_pos, gun_angle, player_dead_angle, player_angle
    life = 5
    score = 0
    missed_bullets = 0
    game_over = False
    player_pos[:] = [0, 0]
    gun_angle = 0
    player_angle = 0
    player_dead_angle = 0
    init_enemies()

#---------------------given template ---------------------------------

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
        px, py = player_pos #first person view
        cosg = math.cos(math.radians(gun_angle))
        sing = math.sin(math.radians(gun_angle))

        global cheat_cam_anchor_pos, cheat_cam_anchor_target
        if cheat_mode and cheat_vision and cheat_cam_anchor_pos is not None and cheat_cam_anchor_target is not None:
            ax, ay, az = cheat_cam_anchor_pos  #above head for V key 
            tx, ty, tz = cheat_cam_anchor_target
            gluLookAt(ax, ay, az, tx, ty, tz, 0, 0, 1)
        else:
            eye_z = 60 #first person 
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
    global cheat_cam_anchor_pos, cheat_cam_anchor_target, player_angle

    if key == b'w':
        # move using player_angle (independent of gun auto-rotation)
        player_pos[0] += PLAYER_SPEED * math.cos(math.radians(player_angle))
        player_pos[1] += PLAYER_SPEED * math.sin(math.radians(player_angle))
    elif key == b's':
        player_pos[0] -= PLAYER_SPEED * math.cos(math.radians(player_angle))
        player_pos[1] -= PLAYER_SPEED * math.sin(math.radians(player_angle))
    elif key == b'a':
        # manual rotate affects both gun and player facing
        gun_angle += 5
        player_angle += 5
    elif key == b'd':
        gun_angle -= 5
        player_angle -= 5
    elif key == b'c':
        cheat_mode = not cheat_mode
        if not cheat_mode:
            cheat_vision = False
            cheat_cam_anchor_pos = None
            cheat_cam_anchor_target = None
    elif key == b'v' and cheat_mode and camera_mode == 1:
        cheat_vision = not cheat_vision
        if cheat_vision:
            head_z = 35
            anchor_height = head_z + 70
            ax = player_pos[0]
            ay = player_pos[1]
            az = anchor_height
            cosg = math.cos(math.radians(gun_angle))
            sing = math.sin(math.radians(gun_angle))
            tx = player_pos[0] + 50 * cosg
            ty = player_pos[1] + 50 * sing
            tz = head_z
            cheat_cam_anchor_pos = (ax, ay, az)
            cheat_cam_anchor_target = (tx, ty, tz)
        else:
            cheat_cam_anchor_pos = None
            cheat_cam_anchor_target = None
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
    global player_dead_angle, game_over
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



