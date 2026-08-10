import os
import time
import math
import colorama

colorama.init()

size = 10
values = [0 for _ in range(size**2)]
fps = 2
middle = size // 2
edger = size
edgel = 0

brightnesasciiseffect = ".;*#&@"
current_color = None

RENDER_MODE = "terminal"
win_handle = None

def init_window(scale=30):
    """Initializes a hardware-accelerated OpenGL window backend using Pygame."""
    global RENDER_MODE, win_handle
    import pygame
    from OpenGL.GL import (
        glViewport, glMatrixMode, glLoadIdentity, glOrtho,
        glEnable, glGenTextures, glBindTexture, glTexImage2D,
        glTexParameteri, glClear, glBegin, glEnd, glTexCoord2f,
        glVertex2f, GL_PROJECTION, GL_MODELVIEW, GL_TEXTURE_2D,
        GL_RGB, GL_UNSIGNED_BYTE, GL_NEAREST, GL_TEXTURE_MIN_FILTER,
        GL_TEXTURE_MAG_FILTER, GL_COLOR_BUFFER_BIT, GL_QUADS
    )

    RENDER_MODE = "window"

    pygame.init()
    info = pygame.display.Info()
    screen_w, screen_h = info.current_w, info.current_h
    max_dim = min(screen_w, screen_h) * 0.85

    if size * scale > max_dim:
        scale = max(1, int(max_dim / size))

    canvas_dim = size * scale
    pygame.display.set_mode((canvas_dim, canvas_dim), pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption("Drawer Engine Window (OpenGL GPU)")

    glViewport(0, 0, canvas_dim, canvas_dim)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, canvas_dim, canvas_dim, 0, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glEnable(GL_TEXTURE_2D)
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

    win_handle = {
        'scale': scale,
        'canvas_dim': canvas_dim,
        'tex_id': tex_id,
        'last_key': "",
        'pygame': pygame,
        'gl': {
            'glClear': glClear,
            'glBindTexture': glBindTexture,
            'glTexImage2D': glTexImage2D,
            'glBegin': glBegin,
            'glEnd': glEnd,
            'glTexCoord2f': glTexCoord2f,
            'glVertex2f': glVertex2f,
            'GL_TEXTURE_2D': GL_TEXTURE_2D,
            'GL_RGB': GL_RGB,
            'GL_UNSIGNED_BYTE': GL_UNSIGNED_BYTE,
            'GL_COLOR_BUFFER_BIT': GL_COLOR_BUFFER_BIT,
            'GL_QUADS': GL_QUADS
        }
    }

def switch_color(r=None, g=None, b=None):
    global current_color
    if r is None or g is None or b is None:
        current_color = None
    else:
        r = max(0, min(255, int(r)))
        g = max(0, min(255, int(g)))
        b = max(0, min(255, int(b)))
        current_color = (r, g, b)

def get_color_val(activation_value):
    if activation_value == 0:
        return 0
    if current_color is None:
        return activation_value
    return (activation_value, current_color)

def update_specs(values=None):
    global middle, edger
    middle = size // 2
    edger = size

def draw_screen_ascii(screen_values=None):
    """
    Renders direct terminal text with 24-bit ANSI colors regardless of 
    whether RENDER_MODE is set to 'window' or 'terminal'.
    """
    if screen_values is None:
        screen_values = values

    screen = ""
    for index, cell in enumerate(screen_values):
        if index % size == 0 and index != 0:
            screen += '\n'
        
        if isinstance(cell, tuple):
            brightness, (r, g, b) = cell
        else:
            brightness = cell
            r, g, b = None, None, None

        if brightness == 0:
            screen += "  "
        elif 1 <= brightness <= 6:
            char = brightnesasciiseffect[brightness - 1]
            if r is not None:
                screen += f"\033[38;2;{r};{g};{b}m{char} \033[0m"
            else:
                screen += char + " "
        else:
            screen += "  "

    return screen

def drawscreen(screen_values=None):
    if screen_values is None:
        screen_values = values

    if RENDER_MODE == "window" and win_handle:
        pg = win_handle['pygame']
        gl = win_handle['gl']

        # Process window events & track keys
        key_map = {
            pg.K_RIGHT: "right",
            pg.K_LEFT: "left",
            pg.K_UP: "up",
            pg.K_DOWN: "down"
        }
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                exit(0)
            elif event.type == pg.KEYDOWN:
                if event.key in key_map:
                    win_handle['last_key'] = key_map[event.key]
            elif event.type == pg.KEYUP:
                if event.key in key_map and win_handle['last_key'] == key_map[event.key]:
                    win_handle['last_key'] = ""

        # Construct raw pixel buffer for GPU texture upload
        raw_pixels = bytearray(size * size * 3)
        for idx, cell in enumerate(screen_values):
            if isinstance(cell, tuple):
                brightness, (r, g, b) = cell
            else:
                brightness = cell
                r, g, b = (255, 255, 255) if brightness > 0 else (0, 0, 0)

            offset = idx * 3
            raw_pixels[offset] = r
            raw_pixels[offset + 1] = g
            raw_pixels[offset + 2] = b

        gl['glClear'](gl['GL_COLOR_BUFFER_BIT'])
        gl['glBindTexture'](gl['GL_TEXTURE_2D'], win_handle['tex_id'])
        gl['glTexImage2D'](
            gl['GL_TEXTURE_2D'], 0, gl['GL_RGB'], size, size, 0,
            gl['GL_RGB'], gl['GL_UNSIGNED_BYTE'], bytes(raw_pixels)
        )

        cd = win_handle['canvas_dim']
        gl['glBegin'](gl['GL_QUADS'])
        gl['glTexCoord2f'](0, 0); gl['glVertex2f'](0, 0)
        gl['glTexCoord2f'](1, 0); gl['glVertex2f'](cd, 0)
        gl['glTexCoord2f'](1, 1); gl['glVertex2f'](cd, cd)
        gl['glTexCoord2f'](0, 1); gl['glVertex2f'](0, cd)
        gl['glEnd']()

        pg.display.flip()
        return ""

    return draw_screen_ascii(screen_values)

def draw_circle(radius, y, x, activation_value=4):
    val = get_color_val(activation_value)
    for i in range(size):
        for j in range(size):
            distance = ((i - x)**2 + (j - y)**2) ** 0.5
            if distance <= radius:
                idx = i * size + j
                if 0 <= idx < len(values):
                    values[idx] = val

def draw_line(x1, y1, x2, y2, activation_value=3):
    val = get_color_val(activation_value)
    x1, y1 = int(round(x1)), int(round(y1))
    x2, y2 = int(round(x2)), int(round(y2))

    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    curr_x, curr_y = x1, y1

    while True:
        if 0 <= curr_x < size and 0 <= curr_y < size:
            idx = curr_y * size + curr_x
            if 0 <= idx < len(values):
                values[idx] = val

        if curr_x == x2 and curr_y == y2:
            break

        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            curr_x += sx
        if e2 < dx:
            err += dx
            curr_y += sy

def draw_triangle(x1, y1, x2, y2, x3, y3, activation_value=1):
    draw_line(x1, y1, x2, y2, activation_value)
    draw_line(x2, y2, x3, y3, activation_value)
    draw_line(x3, y3, x1, y1, activation_value)

def draw_polygon(sides, x, y, polygon_size, rotation=0, activation_value=5):
    side_angle = 360 / sides
    angle_step = math.radians(side_angle)
    
    vertices = []
    for i in range(sides):
        angle = i * angle_step
        nx = x + math.cos(angle) * polygon_size
        ny = y + math.sin(angle) * polygon_size

        rotated_x = math.cos(rotation) * (nx - x) - math.sin(rotation) * (ny - y) + x
        rotated_y = math.sin(rotation) * (nx - x) + math.cos(rotation) * (ny - y) + y

        vertices.append((int(round(rotated_x)), int(round(rotated_y))))
    
    for i in range(sides):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % sides]
        draw_line(x1, y1, x2, y2, activation_value)

def draw_rectangle(x1, y1, x2, y2, activation_value=2):
    val = get_color_val(activation_value)
    for index in range(len(values)):
        y_value = index // size
        x_value = index % size
        if x1 <= x_value <= x2 and y1 <= y_value <= y2:
            values[index] = val

def make_letter(letter, x, y, width, height, rotation=0, activation_value=5):
    letter_map = {
        'A': [(0, 2), (1, 0), (2, 2), None, (0.5, 1), (1.5, 1)],
        'B': [(0, 0), (0, 2), None, (0, 0), (1, 0.5), (0, 1), None, (0, 1), (1, 1.5), (0, 2)],
        'C': [(2, 0), (0, 0), (0, 2), (2, 2)],
        'D': [(0, 0), (0, 2), None, (0, 0), (1.5, 1), (0, 2)],
        'E': [(2, 0), (0, 0), (0, 2), (2, 2), None, (0, 1), (1.5, 1)],
        'F': [(2, 0), (0, 0), (0, 2), None, (0, 1), (1.5, 1)],
        'G': [(2, 0), (0, 0), (0, 2), (2, 2), (2, 1), (1, 1)],
        'H': [(0, 0), (0, 2), None, (2, 0), (2, 2), None, (0, 1), (2, 1)],
        'I': [(0, 0), (2, 0), None, (1, 0), (1, 2), None, (0, 2), (2, 2)],
        'J': [(0, 0), (2, 0), None, (1, 0), (1, 2), (0, 2), (0, 1.5)],
        'K': [(0, 0), (0, 2), None, (2, 0), (0, 1), (2, 2)],
        'L': [(0, 0), (0, 2), (2, 2)],
        'M': [(0, 2), (0, 0), (1, 1), (2, 0), (2, 2)],
        'N': [(0, 2), (0, 0), (2, 2), (2, 0)],
        'O': [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
        'P': [(0, 2), (0, 0), (2, 0), (2, 1), (0, 1)],
        'Q': [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0), None, (1, 1), (2, 2)],
        'R': [(0, 2), (0, 0), (2, 0), (2, 1), (0, 1), None, (1, 1), (2, 2)],
        'S': [(2, 0), (0, 0), (0, 1), (2, 1), (2, 2), (0, 2)],
        'T': [(0, 0), (2, 0), None, (1, 0), (1, 2)],
        'U': [(0, 0), (0, 2), (2, 2), (2, 0)],
        'V': [(0, 0), (1, 2), (2, 0)],
        'W': [(0, 0), (0, 2), (1, 1), (2, 2), (2, 0)],
        'X': [(0, 0), (2, 2), None, (2, 0), (0, 2)],
        'Y': [(0, 0), (1, 1), (2, 0), None, (1, 1), (1, 2)],
        'Z': [(0, 0), (2, 0), (0, 2), (2, 2)],
    }

    key = letter.upper()
    if key not in letter_map:
        print(f"Letter '{letter}' not supported.")
        return

    cx, cy = 1.0, 1.0
    strokes = letter_map[key]
    current_stroke = []

    def flush_stroke(stroke_points):
        if len(stroke_points) < 2:
            return
        for i in range(len(stroke_points) - 1):
            p1 = stroke_points[i]
            p2 = stroke_points[i+1]
            
            lx1 = (p1[0] - cx) * (width / 2.0)
            ly1 = (p1[1] - cy) * (height / 2.0)
            lx2 = (p2[0] - cx) * (width / 2.0)
            ly2 = (p2[1] - cy) * (height / 2.0)

            rx1 = math.cos(rotation) * lx1 - math.sin(rotation) * ly1
            ry1 = math.sin(rotation) * lx1 + math.cos(rotation) * ly1
            rx2 = math.cos(rotation) * lx2 - math.sin(rotation) * ly2
            ry2 = math.sin(rotation) * lx2 + math.cos(rotation) * ly2

            x1 = int(round(rx1 + x))
            y1 = int(round(ry1 + y))
            x2 = int(round(rx2 + x))
            y2 = int(round(ry2 + y))

            draw_line(x1, y1, x2, y2, activation_value)

    for pt in strokes:
        if pt is None:
            flush_stroke(current_stroke)
            current_stroke = []
        else:
            current_stroke.append(pt)
    
    flush_stroke(current_stroke)

def inp_nb():
    if RENDER_MODE == "window" and win_handle:
        pg = win_handle['pygame']
        for event in pg.event.get(pg.KEYDOWN):
            key_map = {
                pg.K_RIGHT: "right",
                pg.K_LEFT: "left",
                pg.K_UP: "up",
                pg.K_DOWN: "down"
            }
            if event.key in key_map:
                win_handle['last_key'] = key_map[event.key]
        return win_handle['last_key']
    return ""

def watch():
    return time.time()

def clear_screen():
    if RENDER_MODE == "terminal":
        time.sleep(1 / fps)
        os.system('cls' if os.name == 'nt' else 'clear')
