from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random

width, height = 600, 600
points = []
frozen = False
blinking_enabled = False
speed = 2
frame_counter = 0


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = random.choice([-1, 1])
        self.dy = random.choice([-1, 1])
        self.color = (random.random(), random.random(), random.random())
        self.visible = True  # used for blinking

    def move(self):
        if frozen:
            return
        self.x += self.dx * speed
        self.y += self.dy * speed

        # Bounce logic
        if self.x <= 0 or self.x >= width:
            self.dx *= -1
        if self.y <= 0 or self.y >= height:
            self.dy *= -1

    def draw(self):
        if blinking_enabled:
            # Toggle visibility every 30 frames
            self.visible = (frame_counter // 30) % 2 == 0
        else:
            self.visible = True

        if self.visible:
            glColor3f(*self.color)
            glBegin(GL_POINTS)
            glVertex2f(self.x, self.y)
            glEnd()


def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, width, 0, height)
    glPointSize(5)


def display():
    glClear(GL_COLOR_BUFFER_BIT)

    for point in points:
        point.draw()

    glutSwapBuffers()


def idle():
    global frame_counter
    if not frozen:
        frame_counter += 1
        for point in points:
            point.move()
    glutPostRedisplay()


def keyboard(key, x, y):
    global speed, frozen
    if key == b' ':
        frozen = not frozen  # toggle freeze


def special_keys(key, x, y):
    global speed
    if key == GLUT_KEY_UP:
        speed += 1
    elif key == GLUT_KEY_DOWN:
        speed = max(1, speed - 1)


def mouse(button, state, x, y):
    global blinking_enabled
    if state != GLUT_DOWN:
        return

    # Converting from window to OpenGL coords (invert y)
    ogl_x = x
    ogl_y = height - y

    if button == GLUT_RIGHT_BUTTON:
        # Adding a new moving point
        points.append(Point(ogl_x, ogl_y))

    elif button == GLUT_LEFT_BUTTON:
        blinking_enabled = not blinking_enabled



glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
glutInitWindowSize(width, height)
glutCreateWindow(b"Task 2: Amazing Box")
init()
glutDisplayFunc(display)
glutIdleFunc(idle)
glutKeyboardFunc(keyboard)
glutSpecialFunc(special_keys)
glutMouseFunc(mouse)
glutMainLoop()
