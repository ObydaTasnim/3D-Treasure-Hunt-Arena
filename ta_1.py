from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

width, height = 500, 500
extra_margin = 300  # Extra width for diagonal rain
rain_direction = 0
brightness = 1.0

# Raindrops 
raindrops = [(random.randint(-extra_margin, width + extra_margin), random.randint(0, height)) for _ in range(200)]

def init():
    glClearColor(1.0, 1.0, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)

def draw_house():
    glColor3f(0.87, 0.72, 0.53)  # Light brown yellowish
    glBegin(GL_TRIANGLES)
    glVertex2f(150, 100)
    glVertex2f(350, 100)
    glVertex2f(350, 200)
    glVertex2f(150, 100)
    glVertex2f(350, 200)
    glVertex2f(150, 200)
    glEnd()

    glColor3f(0.5, 0.0, 0.0)  # Roof
    glBegin(GL_TRIANGLES)
    glVertex2f(130, 200)
    glVertex2f(370, 200)
    glVertex2f(250, 270)
    glEnd()

    glColor3f(0.0, 1.0, 1.0,)  # Windows (rectangular and symmetric)
    for wx in [170, 290]:  # symmetric positions relative to door
        glBegin(GL_TRIANGLES)
        glVertex2f(wx, 140)
        glVertex2f(wx + 40, 140)
        glVertex2f(wx + 40, 170)
        glVertex2f(wx, 140)
        glVertex2f(wx + 40, 170)
        glVertex2f(wx, 170)
        glEnd()

    glColor3f(1.0, 0.75, 0.8)  # Door
    glBegin(GL_TRIANGLES)
    glVertex2f(230, 100)
    glVertex2f(270, 100)
    glVertex2f(270, 160)
    glVertex2f(230, 100)
    glVertex2f(270, 160)
    glVertex2f(230, 160)
    glEnd()

def draw_tree(base_x, base_y):
 
    for i, width_offset in enumerate([25, 20, 15]):
        glColor3f(0.0, 0.5 + i * 0.1, 0.0)
        glBegin(GL_TRIANGLES)
        glVertex2f(base_x - width_offset, base_y + i * 15)
        glVertex2f(base_x + width_offset, base_y + i * 15)
        glVertex2f(base_x, base_y + 30 + i * 5)
        glEnd()


def draw_soil():
    glColor3f(0.4, 0.25, 0.1)
    glBegin(GL_TRIANGLES)
    glVertex2f(0, 0)
    glVertex2f(width, 0)
    glVertex2f(width, 100)
    glVertex2f(0, 0)
    glVertex2f(width, 100)
    glVertex2f(0, 100)
    glEnd()

def draw_rain():
    glColor3f(0.6, 0.6, 1.0)
    glBegin(GL_LINES)
    for x, y in raindrops:
        glVertex2f(x, y)
        glVertex2f(x + rain_direction, y - 10)
    glEnd()

def update_rain():
    global raindrops
    for i in range(len(raindrops)):
        x, y = raindrops[i]
        y -= 10
        x += rain_direction
        if y < 0 or x < -extra_margin or x > width + extra_margin:
            x = random.randint(-extra_margin, width + extra_margin)
            y = height
        raindrops[i] = (x, y)

def draw_scene():
    global brightness
    glClearColor(brightness, brightness, brightness, 1.0)
    glClear(GL_COLOR_BUFFER_BIT)
    draw_soil()
    # Left side trees
    for x in [30,60, 90, 120]:
        draw_tree(x, 100)
    # Right side trees
    for x in [380, 410, 440,470]:
        draw_tree(x, 100)
    draw_house()
    draw_rain()
    glutSwapBuffers()

def animate():
    update_rain()
    glutPostRedisplay()

def keyboard(key, x, y):
    global brightness
    if key == b'e':
        brightness = max(0.2, brightness - 0.1)
    elif key == b'm':
        brightness = min(1.0, brightness + 0.1)

def special_input(key, x, y):
    global rain_direction
    if key == GLUT_KEY_LEFT:
        rain_direction -= 1
    elif key == GLUT_KEY_RIGHT:
        rain_direction += 1


glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(width, height)
glutInitWindowPosition(100, 100)
glutCreateWindow(b"House in Rainfall")
init()
glutDisplayFunc(draw_scene)
glutIdleFunc(animate)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special_input)
glutMainLoop()





