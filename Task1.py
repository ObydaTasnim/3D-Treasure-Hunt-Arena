# Author: Md Asiful Hasan Asif
# ID: <your_student_id_here>
# Assignment: CSE423 - Lab 1, Task 2: The Amazing Box

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

# Display window dimensions
canvas_width, canvas_height = 600, 600

# Simulation control variables
particles = []
paused = False
flashing_on = False
motion_rate = 2
frame_tick = 0

class BouncerDot:
    """
    Represents a moving particle that bounces within the box.
    Each dot has position, direction, speed, color, and blink state.
    """
    def __init__(self, xpos, ypos):
        self.x = xpos
        self.y = ypos
        self.dx = random.choice([-1, 1])
        self.dy = random.choice([-1, 1])
        self.color = (random.random(), random.random(), random.random())
        self.visible = True

    def move(self):
        if paused:
            return

        self.x += self.dx * motion_rate
        self.y += self.dy * motion_rate

        # Bounce at walls
        if self.x <= 0 or self.x >= canvas_width:
            self.dx *= -1
        if self.y <= 0 or self.y >= canvas_height:
            self.dy *= -1

    def render(self):
        if flashing_on:
            self.visible = (frame_tick // 30) % 2 == 0
        else:
            self.visible = True

        if self.visible:
            glColor3f(*self.color)
            glBegin(GL_POINTS)
            glVertex2f(self.x, self.y)
            glEnd()

def setup_scene():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, canvas_width, 0, canvas_height)
    glPointSize(6)

def draw():
    glClear(GL_COLOR_BUFFER_BIT)

    for particle in particles:
        particle.render()

    glutSwapBuffers()

def refresh():
    global frame_tick
    if not paused:
        frame_tick += 1
        for particle in particles:
            particle.move()
    glutPostRedisplay()

def handle_keyboard(key, x, y):
    global paused
    if key == b' ':
        paused = not paused

def handle_special_keys(key, x, y):
    global motion_rate
    if key == GLUT_KEY_UP:
        motion_rate += 1
    elif key == GLUT_KEY_DOWN:
        motion_rate = max(1, motion_rate - 1)

def mouse_click(button, state, x, y):
    global flashing_on
    if state != GLUT_DOWN:
        return

    ogl_x = x
    ogl_y = canvas_height - y

    if button == GLUT_RIGHT_BUTTON:
        particles.append(BouncerDot(ogl_x, ogl_y))
    elif button == GLUT_LEFT_BUTTON:
        flashing_on = not flashing_on

# OpenGL init

glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(canvas_width, canvas_height)
glutCreateWindow(b"Amazing Box - Task 2")
setup_scene()
glutDisplayFunc(draw)
glutIdleFunc(refresh)
glutKeyboardFunc(handle_keyboard)
glutSpecialFunc(handle_special_keys)
glutMouseFunc(mouse_click)
glutMainLoop()









