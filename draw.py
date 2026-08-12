import re
import base64
import sys
Manager3D = None
import math
import Drawer
import time
import subprocess
import random
import os
import types
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import pyopencl as cl
import keyboard._nixkeyboard

# bypass root check
os.geteuid = lambda: 0

# bypass dumpkeys execution inside desktop terminal
keyboard._nixkeyboard.build_tables = lambda: None
from keyboard._keyboard_event import KEY_DOWN, KEY_UP
import keyboard

try:
    platforms = cl.get_platforms()
    gpu_devices = []
    for platform in platforms:
        gpu_devices.extend(platform.get_devices(device_type=cl.device_type.GPU))
    cl_ctx = cl.Context([gpu_devices[0]]) if gpu_devices else cl.create_some_context()
    cl_queue = cl.CommandQueue(cl_ctx)
except Exception:
    cl_ctx = None
    cl_queue = None

OPENCL_KERNEL_SRC = """
__kernel void transform_points_3d(__global const float* points,
                                 __global float* out_points,
                                 const float scale,
                                 const float pos_x,
                                 const float pos_y,
                                 const float pos_z,
                                 const int num_points) {
    int gid = get_global_id(0);
    if (gid < num_points) {
        out_points[gid * 3 + 0] = pos_x + points[gid * 3 + 0] * scale;
        out_points[gid * 3 + 1] = pos_y + points[gid * 3 + 1] * scale;
        out_points[gid * 3 + 2] = pos_z + points[gid * 3 + 2] * scale;
    }
}

__kernel void render_buffer_to_rgb(__global const int* values,
                                   __global unsigned char* rgb_out,
                                   const int total_cells) {
    int gid = get_global_id(0);
    if (gid < total_cells) {
        int cell = values[gid];
        unsigned char r = 0, g = 0, b = 0;
        if (cell >= 1 && cell <= 6) {
            unsigned char val = (unsigned char)((cell * 255) / 6);
            r = val; g = val; b = val;
        }
        rgb_out[gid * 3 + 0] = r;
        rgb_out[gid * 3 + 1] = g;
        rgb_out[gid * 3 + 2] = b;
    }
}
"""

prg = cl.Program(cl_ctx, OPENCL_KERNEL_SRC).build() if cl_ctx else None

kimp = None

def on_action(event):
    global kimp
    if event.event_type == KEY_DOWN:
        kimp = event.name
    elif event.event_type == KEY_UP:
        if event.name == kimp:
            kimp = None

keyboard.hook(on_action)

def get_key(args):
    global kimp
    return kimp

def get_time(args):
    return time.time()

def wait(args):
    if not args or not args[0]:
        return
    parsed = parse_statement(args[0])
    if parsed is not None:
        val = parsed[0]
        if isinstance(val, (int, float)):
            time.sleep(val / 1000.0)

def clear_screen(args):
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)

def cleardands(args):
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)
    if hasattr(Drawer, "clear_screen"):
        Drawer.clear_screen()
    else:
        Drawer.values_np[:] = 0
    if hasattr(Manager3D, "clear"):
        Manager3D.clear()

def draw_line_func(args):
    if len(args) >= 4:
        brightness = (3, "int")
        p1 = parse_statement(args[0])
        p2 = parse_statement(args[1])
        p3 = parse_statement(args[2])
        p4 = parse_statement(args[3])
        
        if len(args) == 5:
            brightness = parse_statement(args[4])
        
        if p1 and p2 and p3 and p4:
            x1, y1, x2, y2 = int(p1[0]), int(p2[0]), int(p3[0]), int(p4[0])
            b = int(brightness[0]) if brightness else 3
            
            Drawer.draw_line(x1, y1, x2, y2, b)
            
            if hasattr(Manager3D, "draw_line_3d"):
                Manager3D.draw_line_3d(x1, y1, 0, x2, y2, 0)

        if len(args) >= 6:
            p5 = parse_statement(args[4])
            p6 = parse_statement(args[5])
            if hasattr(Manager3D, "draw_line_3d"):
                Manager3D.draw_line_3d(
                    int(p1[0]), int(p2[0]), int(p3[0]), 
                    int(p4[0]), int(p5[0]), int(p6[0])
                )

def update_specs_func(args):
    Drawer.update_specs()

def randoint(args):
    args2 = [parse_statement(arg) for arg in args]
    return random.randint(args2[0][0], args2[1][0])

def updatepos(data, args):
    if len(args) >= 2:
        addend = args[0]
        addend2 = args[1]
        pts = np.array(data[0], dtype=np.float32)
        pts[:, 0] += addend
        pts[:, 1] += addend2
        data[0] = [tuple(p) for p in pts]

def updatespritedata(data, args):
    if not args:
        return
    if all(isinstance(a, (int, float)) for a in args):
        if len(args) == 1:
            data[1] = args[0]
        elif len(args) in (2, 3):
            data[2] = tuple(args)
    elif len(args) == 1 and isinstance(args[0], (tuple, list)):
        data[2] = args[0]
    elif len(args) == 2:
        if isinstance(args[0], (tuple, list)) and isinstance(args[1], (int, float)):
            data[2] = args[0]
            data[1] = args[0]
        elif isinstance(args[0], (int, float)) and isinstance(args[1], (tuple, list)):
            data[1] = args[0]
            data[2] = args[1]

def cleardisp(args):
    if hasattr(Drawer, "clear_screen"):
        Drawer.clear_screen()
    else:
        Drawer.values_np[:] = 0
    if hasattr(Manager3D, "clear"):
        Manager3D.clear()

def drawsprite(data, args):
    is_3D = len(data[0][0]) == 3
    size = float(data[1])
    position = data[2]
    pts = np.array(data[0], dtype=np.float32)

    if cl_ctx and prg:
        num_pts = len(pts)
        out_pts = np.empty_like(pts)
        mf = cl.mem_flags

        if is_3D:
            pts_buf = cl.Buffer(cl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=pts)
            out_buf = cl.Buffer(cl_ctx, mf.WRITE_ONLY, out_pts.nbytes)
            prg.transform_points_3d(
                cl_queue, (num_pts,), None,
                pts_buf, out_buf,
                np.float32(size),
                np.float32(position[0]), np.float32(position[1]), np.float32(position[2]),
                np.int32(num_pts)
            )
            cl.enqueue_copy(cl_queue, out_pts, out_buf)
            
            prevline = out_pts[0]
            for line in out_pts:
                Manager3D.draw_line_3d(
                    int(prevline[0]), int(prevline[1]), int(prevline[2]),
                    int(line[0]), int(line[1]), int(line[2])
                )
                prevline = line
            return

    if is_3D:
        transformed = np.zeros_like(pts)
        transformed[:, 0] = position[0] + pts[:, 0] * size
        transformed[:, 1] = position[1] + pts[:, 1] * size
        transformed[:, 2] = position[2] + pts[:, 2] * size
        prevline = transformed[0]
        for line in transformed:
            Manager3D.draw_line_3d(
                int(prevline[0]), int(prevline[1]), int(prevline[2]),
                int(line[0]), int(line[1]), int(line[2])
            )
            prevline = line
    else:
        transformed = np.zeros_like(pts)
        transformed[:, 0] = position[0] + pts[:, 0] * size
        transformed[:, 1] = position[1] + pts[:, 1] * size
        prevline = transformed[0]
        for line in transformed:
            Drawer.draw_line(
                int(prevline[0]), int(prevline[1]),
                int(line[0]), int(line[1])
            )
            prevline = line

def Display_Screen(args):
    print(Drawer.drawscreen())

def Printout(args):
    if not args or not args[0]:
        print("")
        return
    val = parse_statement(args[0])
    if val is not None:
        print(val[0])
    else:
        print(args[0])

def mutate(args):
    args2 = [parse_statement(arg) for arg in args]
    l = args2[0][0]
    toapp = args2[1][0]
    toval = args2[2][0]
    x = in_variables_index(args[0])
    if x != -1:
        l[int(toapp)] = toval
        variables[x]["data"] = l
        variables[x]["type_data"] = l

def draw_kitty(args):
    total_cells = len(Drawer.values_np)
    
    if cl_ctx and prg and all(isinstance(x, int) for x in Drawer.values_np):
        vals_np = np.array(Drawer.values_np, dtype=np.int32)
        rgb_out = np.empty((total_cells, 3), dtype=np.uint8)
        
        mf = cl.mem_flags
        vals_buf = cl.Buffer(cl_ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=vals_np)
        rgb_buf = cl.Buffer(cl_ctx, mf.WRITE_ONLY, rgb_out.nbytes)
        
        prg.render_buffer_to_rgb(cl_queue, (total_cells,), None, vals_buf, rgb_buf, np.int32(total_cells))
        cl.enqueue_copy(cl_queue, rgb_out, rgb_buf)
        byte_data = rgb_out.tobytes()
    else:
        gray_levels = np.array([0, 42, 85, 128, 170, 213, 255], dtype=np.uint8)
        rgb_buffer = np.zeros((total_cells, 3), dtype=np.uint8)
        
        for idx, cell in enumerate(Drawer.values_np):
            if isinstance(cell, tuple):
                brightness, (r, g, b) = cell
                if brightness != 0:
                    rgb_buffer[idx] = [int(r) & 0xFF, int(g) & 0xFF, int(b) & 0xFF]
            else:
                if 1 <= cell <= 6:
                    val = gray_levels[cell]
                    rgb_buffer[idx] = [val, val, val]
        byte_data = rgb_buffer.tobytes()

    encoded = base64.b64encode(byte_data).decode("ascii")
    sys.stdout.write("\033[H")
    sys.stdout.write(f"\033_Ga=T,f=24,s={Drawer.size},v={Drawer.size};{encoded}\033\\")
    sys.stdout.flush()

def add_to_list(args):
    args2 = [parse_statement(arg) for arg in args]
    l = args2[0][0]
    toapp = args2[1][0]
    x = in_variables_index(args[0])
    if x != -1:
        l.append(toapp)
        variables[x]["data"] = l
        variables[x]["type_data"] = l

def pap(args):
    global todo
    todo += str(parse_statement(args[0])[0])

def papout(args):
    global todo
    print(todo)
    todo = ""

def papnew(args):
    global todo
    todo += "\n"

def cos(args):
    return math.cos(parse_statement(args[0])[0])

def set_color(args):
    if len(args) > 0:
        args2 = [parse_statement(arg) for arg in args]
        r = args2[0][0]
        g = args2[1][0]
        b = args2[2][0]
        Drawer.switch_color(r, g, b)
    else:
        Drawer.switch_color()

def sin(args):
    return math.sin(parse_statement(args[0])[0])

def edit_screen_size(args):
    parsed = parse_statement(args[0])
    if parsed:
        Drawer.edit_size(int(parsed[0]))

def drawin(args):
    Drawer.drawscreen()
    if hasattr(Manager3D, "display"):
        Manager3D.display()

def init(args):
    p_title = parse_statement(args[0])
    p_width = parse_statement(args[1])
    p_height = parse_statement(args[2])
    p_scale = parse_statement(args[3])
    
    title = p_title[0] if p_title else str(args[0])
    width = p_width[0] if p_width else int(args[1])
    height = p_height[0] if p_height else int(args[2])
    scale = p_scale[0] if p_scale else int(args[3])

    Drawer.init_window(scale, None, title, width, height)

printhello = lambda args: print("Hello to you!")
todo = ""

CFuncs = {
    "hello": printhello,
    "display": Display_Screen,
    "pout": Printout,
    "wait": wait,
    "clr": clear_screen,
    "clrd": cleardisp,
    "clrds": cleardands,
    "editsize": edit_screen_size,
    "inp": get_key,
    "drlin": draw_line_func,
    "updspec": update_specs_func,
    "addend": add_to_list,
    "cos": cos,
    "sin": sin,
    "papp": pap,
    "pappout": papout,
    "pappnew": papnew,
    "mut": mutate,
    "genint": randoint,
    "setco": set_color,
    "dispkit": draw_kitty,
    "watch": get_time,
    "rendwin": drawin,
    "init": init
}

user_functions = {}

var_map = {}
watch = {}
variables = [
    {
        "name": "square", 
        "type": "sprite", 
        "data": [[(-1, 1), (1, 1), (1, -1), (-1, -1), (-1, 1)], 1, [0, 0], "square"],
        "properties": {
            "draw": drawsprite,
            "upd": updatespritedata,
            "updpos": updatepos,
        },
    },
]

for idx, v in enumerate(variables):
    var_map[v["name"]] = idx

def in_variables_index(name):
    return var_map.get(name, -1)

def in_variables(name):
    idx = var_map.get(name, -1)
    return variables[idx] if idx != -1 else None

class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

def call_user_function(func_name, raw_args):
    global user_functions, variables, var_map
    func = user_functions[func_name]
    params = func["params"]
    ret_type = func["return_type"]
    body = func["body"]

    parsed_args = []
    if raw_args:
        for arg in raw_args:
            p = parse_statement(arg)
            parsed_args.append(p[0] if p is not None else None)

    old_variables = list(variables)
    old_var_map = dict(var_map)

    for param_name, arg_val in zip(params, parsed_args):
        p_type = "str" if isinstance(arg_val, str) else ("int" if isinstance(arg_val, int) else ("float" if isinstance(arg_val, float) else "str"))
        idx = len(variables)
        v_obj = {
            "name": param_name,
            "type": p_type,
            "data": arg_val,
            "type_data": arg_val
        }
        variables.append(v_obj)
        var_map[param_name] = idx

    return_val = None
    try:
        run_block(body)
    except ReturnValue as ret:
        return_val = ret.value
    finally:
        variables = old_variables
        var_map = old_var_map

    return (return_val, ret_type)

RE_STRING = re.compile(r"^['\"](.*)['\"]$")
RE_INTEGER = re.compile(r"(^[+-]?\d+)$")
RE_LIST = re.compile(r"^[\{\(](.+)[\}\)]$")
RE_BOOL = re.compile(r"(^true|false$)")
RE_FLOAT = re.compile(r"(^[+-]?[0-9]*\.[0-9]+|[0-9]+\.[0-9]*)$")
RE_CUFUNC = re.compile(r'^\*(.+?)\*\((.*)\)$')
RE_POSSIBLEINDENT = re.compile(r"^(.+)\[(.+)\]$")

def parse_statement(state):
    global CFuncs, user_functions
    if state is None:
        return ("", "str")
    state = str(state).strip()
    if not state:
        return ("", "str")

    STRING = RE_STRING.match(state)
    if STRING:
        return (STRING.group(1), "str")

    if state.isdigit() or (state.startswith('-') and state[1:].isdigit()):
        return (int(state), "int")

    v = in_variables(state)
    if v is not None:
        val = v.get("type_data", v.get("data"))
        val_type = v.get("type", type(val).__name__)
        return (val, val_type)

    INTEGER = RE_INTEGER.match(state)
    LIST = RE_LIST.match(state)
    BOOL = RE_BOOL.match(state)
    FLOAT = RE_FLOAT.match(state)
    CuFunc = RE_CUFUNC.match(state)
    POSSIBLEINDENT = RE_POSSIBLEINDENT.match(state)

    if LIST:
        listreturn = []
        for item in LIST.group(1).split(","):
            item = item.strip()
            if item:
                parsed = parse_statement(item)
                if parsed:
                    listreturn.append(parsed[0])
                else:
                    listreturn.append(item) 
        return (listreturn, "list")
    if FLOAT:
        return (float(FLOAT.group(1)), "float")
    if INTEGER:
        return (int(INTEGER.group(1)), "int")
    if BOOL:
        bok = BOOL.group(1)
        return (True if bok == "true" else False, "bool")

    if CuFunc:
        func_name = CuFunc.group(1)
        raw_args = CuFunc.group(2).strip()
        args = [a.strip() for a in raw_args.split(",")] if raw_args else []
        if func_name in CFuncs:
            res = CFuncs[func_name](args)
            res = "" if res is None else res
            return (res, type(res).__name__)
        elif func_name in user_functions:
            return call_user_function(func_name, args)

    if "." in state and not FLOAT:
        var_name = state.split(".")[0]
        v = in_variables(var_name)
        if v and "properties" in v:
            properti = state.split(".")[1]
            if properti in v["properties"]:
                prop = v["properties"][properti]
                if isinstance(prop, types.FunctionType):
                    hi = prop()
                    return (hi, type(hi).__name__)
                else:
                    return (prop, type(prop).__name__)

    if "not" in state:
        parts = state.split("not", 1)
        p = parse_statement(parts[1])
        left_val = p[0] if p else None
        return (not left_val, "bool")

    for op in ["and", "or"]:
        if op in state:
            parts = state.split(op, 1)
            left_p = parse_statement(parts[0])
            right_p = parse_statement(parts[1])
            left_val = left_p[0] if left_p else None
            right_val = right_p[0] if right_p else None

            if op == "and": return (left_val and right_val, "bool")
            if op == "or": return (left_val or right_val, "bool")

    for op in ["==", "!=", "<=", ">=", "<", ">"]:
        if op in state:
            parts = state.split(op, 1)
            left_p = parse_statement(parts[0])
            right_p = parse_statement(parts[1])
            left_val = left_p[0] if left_p else None
            right_val = right_p[0] if right_p else None
            if left_val is None or right_val is None:
                left_val = left_val if left_val is not None else 0
                right_val = right_val if right_val is not None else 0
            if op == "==": return (left_val == right_val, "bool")
            if op == "!=": return (left_val != right_val, "bool")
            if op == "<=": return (left_val <= right_val, "bool")
            if op == ">=": return (left_val >= right_val, "bool")
            if op == "<": return (left_val < right_val, "bool")
            if op == ">": return (left_val > right_val, "bool")

    for op in ["+", "-", "*", "/", "%"]:
        if op in state and not (op in ("+", "-") and re.match(r"^[+-]?\d+(\.\d+)?$", state)):
            parts = state.rsplit(op, 1)
            left_p = parse_statement(parts[0])
            right_p = parse_statement(parts[1])
            
            if left_p is not None and right_p is not None:
                l_val, r_val = left_p[0], right_p[0]
                try:
                    if op == "+": res = l_val + r_val
                    elif op == "-" and not INTEGER: res = l_val - r_val
                    elif op == "*": res = l_val * r_val
                    elif op == "/": res = l_val / r_val
                    elif op == "%":
                        if isinstance(l_val, list):
                            l_val = l_val[0]
                        res = l_val % r_val
                    res_type = "float" if isinstance(res, float) else "int"
                except Exception:
                    res = 0
                    res_type = "int"
                return (res, res_type)

    if POSSIBLEINDENT:
        var = POSSIBLEINDENT.group(1)
        ind = POSSIBLEINDENT.group(2)
        var = parse_statement(var)
        if var:
            if var[1] == "list":
                return parse_statement(var[0][int(parse_statement(ind)[0])])
            elif var[1] == "str":
                return var[0][parse_statement(ind)[0]]

    return None

RE_DECLARE = re.compile(r"^([a-zA-Z_]\w*)\s*:\s*(int|str|string|list|float|bool)\s+(.+)$")
RE_WATCH = re.compile(r"^watch ([a-zA-Z_]\w*)\s*:\s*(int|str|string|list|float|bool)\s+(.+)\s+\[(.+)\]")
RE_UNWATCH = re.compile(r"^unwatch (.+)$")
RE_CUSTOMFUNC = re.compile(r'^\*(.+?)\*\((.*)\)$')

def execute_line(line, i):
    if line.startswith("import "):
        module_name = line.split()[1]
        globals()[module_name] = __import__(module_name)
        return

    if line.startswith("return"):
        expr = line[6:].strip()
        val = parse_statement(expr)[0] if expr else None
        raise ReturnValue(val)

    Declare = RE_DECLARE.match(line)
    DeclareWatch = RE_WATCH.match(line)
    CustomFunc = RE_CUSTOMFUNC.match(line)
    
    if Declare:
        var_name = Declare.group(1).strip()
        type_name = "str" if Declare.group(2) == "string" else Declare.group(2)
        parsed_val = parse_statement(Declare.group(3))
        creation = False
        oldval = None
        if parsed_val is not None:
            idx = in_variables_index(var_name)
            val = parsed_val[0]
            
            if idx != -1:
                oldval = variables[idx]["data"]
                variables[idx]["type_data"] = val
                variables[idx]["data"] = val
                variables[idx]["type"] = type_name
            else:
                creation = True
                new_idx = len(variables)
                variables.append({
                    "name": var_name,
                    "type": type_name,
                    "data": val,
                    "type_data": val
                })
                var_map[var_name] = new_idx
            if var_name in watch and oldval is not None:
                for line_item in watch[var_name]:
                    event = line_item.split(":")
                    action = event[1]
                    event = event[0]
                    event, action = event.strip(), action.strip()
                    maxi = re.match(r"on_max\((.+)\)", event)
                    mini = re.match(r"on_min\((.+)\)", event)
                    if event == "on_change" and not val == oldval and not creation:
                        parse_statement(action)
                    if maxi and val >= parse_statement(maxi.group(1))[0]:
                        parse_statement(action)
                    if mini and val <= parse_statement(mini.group(1))[0]:
                        parse_statement(action)
        return

    if RE_UNWATCH.match(line):
        hi = RE_UNWATCH.match(line)
        to = hi.group(1).strip()
        if to in watch:
            del watch[to]
        return

    if DeclareWatch:
        var_name = DeclareWatch.group(1).strip()
        type_name = "str" if DeclareWatch.group(2) == "string" else DeclareWatch.group(2)
        parsed_val = parse_statement(DeclareWatch.group(3))
        towatch = DeclareWatch.group(4).split(";")
        
        if parsed_val is not None:
            idx = in_variables_index(var_name)
            val = parsed_val[0]
            if idx != -1:         
                variables[idx]["type_data"] = val
                variables[idx]["data"] = val
                variables[idx]["type"] = type_name
            else:
                new_idx = len(variables)
                variables.append({
                    "name": var_name,
                    "type": type_name,
                    "data": val,
                    "type_data": val
                })
                var_map[var_name] = new_idx
            
                watch[var_name] = towatch
            
        return

    if CustomFunc:
        func_name = CustomFunc.group(1)
        raw_args = CustomFunc.group(2).strip()
        args = [a.strip() for a in raw_args.split(",")] if raw_args else []
        if func_name in CFuncs:
            CFuncs[func_name](args)
        elif func_name in user_functions:
            call_user_function(func_name, args)
        return

    if in_variables(line.split(".")[0]) is not None:
        x = in_variables(line.split(".")[0])
        if "." in line:
            properties = x.get("properties", {})
            func_part = line.split(".")[1]
            
            if "(" in func_part and func_part.endswith(")"):
                name = func_part[:func_part.index("(")]
                args_raw = func_part[func_part.index("(")+1:-1]
                
                hello = []
                if args_raw.strip():
                    for item in args_raw.split(","):
                        item = item.strip()
                        if not item: continue
                        
                        parsed = parse_statement(item)
                        if parsed is not None:
                            hello.append(parsed[0])
                        else:
                            raise ValueError(f"Could not parse argument '{item}': Not a literal or known variable.")
                
                if name in properties:
                    properties[name](x["data"], hello)
                return
    
    if not parse_statement(line):
        raise NameError(f"Unknown Statement on line {i}: {line}")

RE_FUNC_MATCH = re.compile(r"^(int|str|string|list|float|bool|void)\s+([a-zA-Z_]\w*)\s*\((.*)\)\s*\[$")
RE_BLOCK_MATCH = re.compile(r"^(if|for|while|match)\s*\((.+)\)\s*\[$")
RE_ONE_LINED = re.compile(r"^(if)\s*\((.+?)\)\s*\[(.+?)\]$")
RE_CASE = re.compile(r"case\s+(.+?)\s*\[\s*(.+?)\s*\]")
RE_DEFAULT = re.compile(r"^default\s*\[\s*(.+)\s*\]$")

def run_block(lines):
    i = 0
    while i < len(lines):
        line = lines[i]
        line = line.split("/-")[0].strip()
        if not line:
            i += 1
            continue
        
        func_match = RE_FUNC_MATCH.match(line)
        block_match = RE_BLOCK_MATCH.match(line)
        one_lined = RE_ONE_LINED.match(line)
        
        if func_match:
            ret_type = func_match.group(1)
            func_name = func_match.group(2)
            raw_params = func_match.group(3).strip()
            params = [p.strip() for p in raw_params.split(",")] if raw_params else []
            
            block_lines = []
            bracket_count = 1
            i += 1
            while i < len(lines) and bracket_count > 0:
                curr = lines[i]
                if curr.endswith("["):
                    bracket_count += 1
                elif curr == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        break
                block_lines.append(curr)
                i += 1
            
            user_functions[func_name] = {
                "return_type": ret_type,
                "params": params,
                "body": block_lines
            }
        elif block_match:
            keyword = block_match.group(1)
            condition_str = block_match.group(2)
            
            block_lines = []
            bracket_count = 1
            i += 1
            while i < len(lines) and bracket_count > 0:
                curr = lines[i]
                if curr.endswith("["):
                    bracket_count += 1
                elif curr == "]":
                    bracket_count -= 1
                    if bracket_count == 0:
                        break
                block_lines.append(curr)
                i += 1
            
            if keyword == "if":
                cond_val = parse_statement(condition_str)[0]
                if cond_val:
                    run_block(block_lines)
            elif keyword == "for":
                loop_val = parse_statement(condition_str)[0]
                if isinstance(loop_val, int):
                    iterable = range(loop_val)
                else:
                    iterable = loop_val
                for _ in iterable:
                    run_block(block_lines)
            elif keyword == "match":
                variable = parse_statement(condition_str)[0]
                matched = False
                for b_line in block_lines:
                    wow = RE_CASE.match(b_line)
                    default = RE_DEFAULT.match(b_line)
                    if wow:
                        matching = wow.group(1)
                        state = wow.group(2)
                        if variable == parse_statement(matching)[0]:
                            matched = True
                            run_block(state.split(";"))
                            break
                    if default:
                        if not matched:
                            run_block(default.group(1).split(";"))
                            break

            elif keyword == "while":
                while parse_statement(condition_str)[0]:
                    run_block(block_lines)
        elif one_lined:
            condition_str = one_lined.group(2)
            evaluation = one_lined.group(3)
            cond_val = parse_statement(condition_str)[0]
            if cond_val:
                run_block(evaluation.split(";"))
        else:
            execute_line(line, i)
        i += 1

def run_script(filename):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('/-')]
    run_block(lines)

run_script("Test.draw") # Put your .draw code here!
