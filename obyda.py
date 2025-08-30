# DISPLAY
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