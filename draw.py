import os
import time
import math
import colorama

size = 10
values = [0 for _ in range(size**2)]
fps = 2  # Fixed typo
MIDDLE = size // 2
EDGERIGHT = size
EDGELEFT = 0

brightnesasciiseffect = ".;*#&@"


def drawscreen(values):
    screen = ""
    for index, value in enumerate(values):
        if index % size == 0:
            screen += '\n'
        elif value == 0:
            screen += "  "
        elif value <= 6:
            screen += brightnesasciiseffect[value - 1] + " "
        elif len(str(value)) == 2:
            ind,color = list(str(value))
            ind = int(ind)
            color = int(color)
            if color == 1:
                screen += colorama.Fore.BLUE + brightnesasciiseffect[ind - 1] + " " + colorama.Fore.RESET
            elif color == 2:
                screen += colorama.Fore.GREEN + brightnesasciiseffect[ind - 1] + " " + colorama.Fore.RESET
            elif color == 3:
                screen += colorama.Fore.RED + brightnesasciiseffect[ind - 1] + " " + colorama.Fore.RESET

    return screen


def draw_circle(radius, y, x, activation_value=4):
    for i in range(size):
        for j in range(size):
            distance = ((i - x)**2 + (j - y)**2) ** 0.5
            if distance <= radius:
                values[i * size + j] = activation_value


def draw_line(x1, y1, x2, y2, activation_value=3):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy
    loops = 0
    while True:
        loops += 1
        if 0 <= x1 < size and 0 <= y1 < size and int(y1 * size + x1) < len(values):
            values[int(y1 * size + x1)] = activation_value
        if x1 == x2 and y1 == y2:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x1 += sx
        if e2 < dx:
            err += dx
            y1 += sy

        if loops > 3000:
            break

def draw_triangle(x1, y1, x2, y2, x3, y3, activation_value=1):
    draw_line(x1, y1, x2, y2, activation_value)
    draw_line(x2, y2, x3, y3, activation_value)
    draw_line(x3, y3, x1, y1, activation_value)

def draw_polygon(sides, x, y, size, rotation=0, activation_value=5):
    side_angle = 360 / sides
    angle_step = math.radians(side_angle)
    
    vertices = []
    for i in range(sides):
        # Calculate the unrotated vertex position
        angle = i * angle_step
        nx = x + math.cos(angle) * size
        ny = y + math.sin(angle) * size

        # Apply rotation to the vertex
        rotated_x = math.cos(rotation) * (nx - x) - math.sin(rotation) * (ny - y) + x
        rotated_y = math.sin(rotation) * (nx - x) + math.cos(rotation) * (ny - y) + y

        # Round to integer coordinates for screen display
        vertices.append((int(rotated_x), int(rotated_y)))
    
    # Draw edges between consecutive vertices
    for i in range(sides):
        x1, y1 = vertices[i]
        x2, y2 = vertices[(i + 1) % sides]  # Connect last vertex to the first
        draw_line(x1, y1, x2, y2, activation_value)

def draw_rectangle(x1, y1, x2, y2, activation_value=2):
    for index, value in enumerate(values):
        y_value = index // size
        x_value = index % size
        if x1 <= x_value <= x2 and y1 <= y_value <= y2:
            values[index] = activation_value


import math

def make_letter(letter, x, y, size, rotation=0, activation_value=5):
    letter_map = {
        'A': [(0, 1), (1, 0), (2, 1), (1, 2), (1, 1)],
        'B': [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (0, 1)],
        'C': [(1, 0), (0, 0), (0, 1), (0, 2), (1, 2)],
        'D': [(0, 0), (0, 2), (1, 0), (1, 2), (0, 1)],
        'E': [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)],
        'F': [(0, 0), (0, 2), (1, 0), (1, 1)],
        'G': [(1, 0), (0, 0), (0, 1), (1, 1), (1, 2), (0, 2)],
        'H': [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
        'I': [(0, 0), (1, 0), (1, 1), (1, 2), (0, 2)],
        'J': [(1, 0), (2, 0), (2, 1), (1, 2), (0, 2)],
        'K': [(0, 0), (0, 2), (1, 1), (2, 0), (2, 2)],
        'L': [(0, 0), (0, 2), (1, 2)],
        'M': [(0, 2), (0, 0), (1, 1), (2, 0), (2, 2)],
        'N': [(0, 2), (0, 0), (2, 2), (2, 0)],
        'O': [(0, 1), (1, 0), (2, 1), (1, 2), (0, 1)],
        'P': [(0, 0), (0, 2), (1, 0), (1, 1), (0, 1)],
        'Q': [(0, 1), (1, 0), (2, 1), (1, 2), (0, 1), (1.5, 1.5), (2, 2)],
        'R': [(0, 0), (0, 2), (1, 0), (1, 1), (0, 1), (1, 2)],
        'S': [(1, 0), (0, 0), (0, 1), (1, 1), (1, 2), (0, 2)],
        'T': [(0, 0), (2, 0), (1, 0), (1, 1), (1, 2)],
        'U': [(0, 0), (0, 2), (1, 2), (2, 2), (2, 0)],
        'V': [(0, 0), (1, 2), (2, 0)],
        'W': [(0, 0), (0, 2), (1, 1), (2, 2), (2, 0)],
        'X': [(0, 0), (2, 2), (1, 1), (0, 2), (2, 0)],
        'Y': [(0, 0), (1, 1), (2, 0), (1, 1), (1, 2)],
        'Z': [(0, 0), (2, 0), (0, 2), (2, 2)],
    }

    if letter.upper() not in letter_map:
        print(f"Letter '{letter}' not supported.")
        return

    scaled_rotated_points = []
    for px, py in letter_map[letter.upper()]:
        sx = px * size
        sy = py * size

        rx = math.cos(rotation) * sx - math.sin(rotation) * sy
        ry = math.sin(rotation) * sx + math.cos(rotation) * sy

        scaled_rotated_points.append((int(rx + x), int(ry + y)))


    for i in range(len(scaled_rotated_points) - 1):
        x1, y1 = scaled_rotated_points[i]
        x2, y2 = scaled_rotated_points[i + 1]
        draw_line(x1, y1, x2, y2, activation_value)

    if letter.upper() in "AOPQ":
        x1, y1 = scaled_rotated_points[0]
        x2, y2 = scaled_rotated_points[-1]
        draw_line(x1, y1, x2, y2, activation_value)
 
    

def clear_screen():
    time.sleep(1 / fps)
    os.system('cls' if os.name == 'nt' else 'clear')


