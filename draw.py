import os
import time
import math
import colorama
import numpy as np

colorama.init()

size = 10
values_np = np.zeros(size * size, dtype=np.float32)
fps = 60
middle = size // 2
edger = size
edgel = 0

brightnesasciiseffect = ".;*#&@"
current_color = (255, 255, 255)

RENDER_MODE = "terminal"
win_handle = None

cl_ctx = None
cl_queue = None
cl_prg = None

def init_cl():
    global cl_ctx, cl_queue, cl_prg
    try:
        import pyopencl as cl
        platforms = cl.get_platforms()
        gpu_devices = []
        for p in platforms:
            gpu_devices.extend(p.get_devices(device_type=cl.device_type.GPU))
        
        ctx_target = gpu_devices[0] if gpu_devices else None
        if ctx_target:
            cl_ctx = cl.Context([ctx_target])
        else:
            cl_ctx = cl.create_some_context()
            
        cl_queue = cl.CommandQueue(cl_ctx)

        kernel_code = """
        __kernel void process_pixels(
            __global const float* input_vals,
            __global unsigned char* output_rgb,
            const int width,
            const int r_in,
            const int g_in,
            const int b_in
        ) {
            int gid = get_global_id(0);
            float val = input_vals[gid];
            
            int offset = gid * 3;
            if (val <= 0.0f) {
                output_rgb[offset]     = 0;
                output_rgb[offset + 1] = 0;
                output_rgb[offset + 2] = 0;
            } else {
                float factor = clamp(val / 6.0f, 0.0f, 1.0f);
                output_rgb[offset]     = (unsigned char)(r_in * factor);
                output_rgb[offset + 1] = (unsigned char)(g_in * factor);
                output_rgb[offset + 2] = (unsigned char)(b_in * factor);
            }
        }
        """
        cl_prg = cl.Program(cl_ctx, kernel_code).build()
    except Exception as e:
        cl_ctx = None

init_cl()

def set_window_icon(icon_path):
    if RENDER_MODE == "window" and win_handle:
        pg = win_handle['pygame']
        if os.path.exists(icon_path):
            icon_surf = pg.image.load(icon_path)
            pg.display.set_icon(icon_surf)

def init_window(scale=30, icon_path="DrawLogo.png",titlename="Draw",width=300,height=300):
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
    
    if icon_path and os.path.exists(icon_path):
        icon_surf = pygame.image.load(icon_path)
        pygame.display.set_icon(icon_surf)

    info = pygame.display.Info()
    screen_w, screen_h = width, height
    max_dim = min(screen_w, screen_h) * 0.85

    if size * scale > max_dim:
        scale = max(1, int(max_dim / size))

    canvas_dim = size * scale
    pygame.display.set_mode((canvas_dim, canvas_dim), pygame.DOUBLEBUF | pygame.OPENGL)
    pygame.display.set_caption(titlename)

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
        'raw_rgb_buffer': np.zeros(size * size * 3, dtype=np.uint8),
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
        current_color = (255, 255, 255)
    else:
        current_color = (max(0, min(255, int(r))), max(0, min(255, int(g))), max(0, min(255, int(b))))

def get_color_val(activation_value):
    return activation_value

def update_specs(values=None):
    global middle, edger
    middle = size // 2
    edger = size

def draw_screen_ascii(screen_values=None):
    if screen_values is None:
        screen_values = values_np

    screen = ""
    for index, val in enumerate(screen_values):
        if index % size == 0 and index != 0:
            screen += '\n'
        
        brightness = int(val)
        if brightness <= 0:
            screen += "  "
        elif 1 <= brightness <= 6:
            char = brightnesasciiseffect[brightness - 1]
            r, g, b = current_color
            screen += f"\033[38;2;{r};{g};{b}m{char} \033[0m"
        else:
            screen += "  "

    return screen

def drawscreen(screen_values=None):
    global values_np
    if screen_values is None:
        screen_values = values_np

    if RENDER_MODE == "window" and win_handle:
        pg = win_handle['pygame']
        gl = win_handle['gl']

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

        rgb_out = win_handle['raw_rgb_buffer']
        
        if cl_ctx and cl_prg:
            import pyopencl as cl
            mf = cl.mem_flags
            in_buf = cl.Buffer(cl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=screen_values)
            out_buf = cl.Buffer(cl_ctx, mf.WRITE_ONLY, rgb_out.nbytes)
            
            r, g, b = current_color
            cl_prg.process_pixels(
                cl_queue, (size * size,), None,
                in_buf, out_buf,
                np.int32(size), np.int32(r), np.int32(g), np.int32(b)
            )
            cl.enqueue_copy(cl_queue, rgb_out, out_buf)
        else:
            scaled = np.clip(screen_values / 6.0, 0, 1)
            rgb_arr = win_handle['raw_rgb_buffer'].reshape((size * size, 3))
            rgb_arr[:, 0] = (scaled * current_color[0]).astype(np.uint8)
            rgb_arr[:, 1] = (scaled * current_color[1]).astype(np.uint8)
            rgb_arr[:, 2] = (scaled * current_color[2]).astype(np.uint8)

        gl['glClear'](gl['GL_COLOR_BUFFER_BIT'])
        gl['glBindTexture'](gl['GL_TEXTURE_2D'], win_handle['tex_id'])
        gl['glTexImage2D'](
            gl['GL_TEXTURE_2D'], 0, gl['GL_RGB'], size, size, 0,
            gl['GL_RGB'], gl['GL_UNSIGNED_BYTE'], rgb_out.tobytes()
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
    grid_y, grid_x = np.ogrid[:size, :size]
    dist = np.sqrt((grid_x - x)**2 + (grid_y - y)**2)
    mask = dist <= radius
    values_np.reshape((size, size))[mask] = activation_value

def draw_line(x1, y1, x2, y2, activation_value=3):
    num_pts = max(abs(x2 - x1), abs(y2 - y1)) * 2 + 1
    xs = np.linspace(x1, x2, num_pts).astype(np.int32)
    ys = np.linspace(y1, y2, num_pts).astype(np.int32)
    valid = (xs >= 0) & (xs < size) & (ys >= 0) & (ys < size)
    indices = ys[valid] * size + xs[valid]
    values_np[indices] = activation_value

def draw_triangle(x1, y1, x2, y2, x3, y3, activation_value=1):
    draw_line(x1, y1, x2, y2, activation_value)
    draw_line(x2, y2, x3, y3, activation_value)
    draw_line(x3, y3, x1, y1, activation_value)

def draw_rectangle(x1, y1, x2, y2, activation_value=2):
    grid = values_np.reshape((size, size))
    grid[max(0, y1):min(size, y2 + 1), max(0, x1):min(size, x2 + 1)] = activation_value

def watch():
    return time.time()

def clear_screen():
    if RENDER_MODE == "terminal":
        time.sleep(1 / fps)
        os.system('cls' if os.name == 'nt' else 'clear')
    else:
        values_np.fill(0)
