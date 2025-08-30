from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

# Window dimensions
width, height = 800, 600

# Rain variables
num_drops = 100
rain_drops = []
rain_dx = 0
rain_dy = -5

# Background and brightness
bg_color = [0.0, 0.0, 0.0]  # night
house_color = [1.0, 1.0, 1.0]  # light walls

def init():
    glClearColor(*bg_color, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

def draw_house():
    glColor3f(*house_color)
    glBegin(GL_QUADS)  # house base
    glVertex2f(300, 150)
    glVertex2f(500, 150)
    glVertex2f(500, 300)
    glVertex2f(300, 300)
    glEnd()

    glColor3f(0.5, 0.2, 0.8)  # roof
    glBegin(GL_TRIANGLES)
    glVertex2f(280, 300)
    glVertex2f(520, 300)
    glVertex2f(400, 400)
    glEnd()

    glColor3f(0.2, 0.6, 1.0)  # door
    glBegin(GL_QUADS)
    glVertex2f(370, 150)
    glVertex2f(430, 150)
    glVertex2f(430, 240)
    glVertex2f(370, 240)
    glEnd()

    glColor3f(0.0, 0.3, 0.8)  # windows
    glBegin(GL_LINES)
    glVertex2f(320, 260); glVertex2f(350, 260)
    glVertex2f(335, 245); glVertex2f(335, 275)
    glVertex2f(450, 260); glVertex2f(480, 260)
    glVertex2f(465, 245); glVertex2f(465, 275)
    glEnd()

def draw_rain():
    glColor3f(0.7, 0.7, 1.0)
    glBegin(GL_LINES)
    for drop in rain_drops:
        x, y = drop
        glVertex2f(x, y)
        glVertex2f(x + rain_dx, y + rain_dy)
    glEnd()

def update_rain():
    global rain_drops
    new_drops = []
    for x, y in rain_drops:
        new_x = x + rain_dx
        new_y = y + rain_dy
        if new_y > 0:
            new_drops.append((new_x, new_y))
        else:
            new_drops.append((random.randint(0, width), height))
    rain_drops = new_drops
    glutPostRedisplay()

def display():
    glClear(GL_COLOR_BUFFER_BIT)
    draw_house()
    draw_rain()
    glutSwapBuffers()

def reshape(w, h):
    global width, height
    width, height = w, h
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

def keyboard(key, x, y):
    global bg_color, house_color
    if key == b'd':  # day
        bg_color = [1.0, 1.0, 1.0]
        house_color[0:3] = [0.0, 0.0, 0.0]
        glClearColor(*bg_color, 1.0)
    elif key == b'n':  # night
        bg_color = [0.0, 0.0, 0.0]
        house_color[0:3] = [1.0, 1.0, 1.0]
        glClearColor(*bg_color, 1.0)
    glutPostRedisplay()

def special_keys(key, x, y):
    global rain_dx
    if key == GLUT_KEY_LEFT:
        rain_dx -= 1
    elif key == GLUT_KEY_RIGHT:
        rain_dx += 1
    glutPostRedisplay()

def timer(v):
    update_rain()
    glutTimerFunc(30, timer, 0)

def main():
    global rain_drops
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(width, height)
    glutCreateWindow(b"Assignment1 Task1 - House with Rain")
    init()
    rain_drops = [(random.randint(0, width), random.randint(0, height)) for _ in range(num_drops)]
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutTimerFunc(30, timer, 0)
    glutMainLoop()

if __name__ == "__main__":
    main()
