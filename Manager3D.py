import Drawer

size = Drawer.size
def draw_line_3d(x1, y1, z1, x2, y2, z2, activation_value=3, fov=5.0):
    # camera/viewer distance offset to prevent division by zero
    depth_offset = fov
    
    # helper for perspective projection
    def project(x, y, z):
        z_adj = z + depth_offset
        if z_adj <= 0:
            z_adj = 0.001
        # map normalized coordinates to your grid dimensions (size)
        px = int((x / z_adj) * (size / 2) + (size / 2))
        py = int((y / z_adj) * (size / 2) + (size / 2))
        return px, py

    # project both 3D endpoints to 2D screen coordinates
    screen_x1, screen_y1 = project(x1, y1, z1)
    screen_x2, screen_y2 = project(x2, y2, z2)

    # use your existing bresenham draw_line function
    Drawer.draw_line(screen_x1, screen_y1, screen_x2, screen_y2, activation_value)

 