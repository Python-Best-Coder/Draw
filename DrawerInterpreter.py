import Drawer
import re
import base64
import sys
import Manager3D
import math
import time
import subprocess
import random
import os
import types
from keyboard._keyboard_event import KEY_DOWN, KEY_UP
import keyboard
kimp = None

def on_action(event):
    global kimp
    if event.event_type == KEY_DOWN:
        kimp = event.name
    
        
    elif event.event_type == KEY_UP:
        # Only reset if the released key matches the stored key
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
    Drawer.values = [0] * len(Drawer.values)

def draw_line_func(args):
    if len(args) >= 4:
        brightness = (3, "int")
        p1 = parse_statement(args[0])
        p2 = parse_statement(args[1])
        p3 = parse_statement(args[2])
        p4 = parse_statement(args[3])
        if len(args) > 4 and not len(args) > 5:
            brightness = parse_statement(args[4])
        if len(args) > 6:
            brightness = parse_statement(args[6])
        
        if p1 and p2 and p3 and p4 and not len(args) > 5:
            Drawer.draw_line(int(p1[0]), int(p2[0]), int(p3[0]), int(p4[0]), int(brightness[0]))
        if len(args) >= 6:
            p5 = parse_statement(args[4])
            p6 = parse_statement(args[5])
            # EXTRACT INTEGER VALUES [0] BEFORE PASSING TO MANAGER3D:
            Manager3D.draw_line_3d(
                int(p1[0]), int(p2[0]), int(p3[0]), 
                int(p4[0]), int(p5[0]), int(p6[0])
            )
            
def update_specs_func(args):
    Drawer.update_specs(Drawer.values)

def randoint(args):
    args2 = [parse_statement(arg) for arg in args]
    return random.randint(args2[0][0],args2[1][0])

def updatepos(data, args):
    global variables
    if len(args) >= 2:
        addend = args[0]
        addend2 = args[1]
        new_data = []
        for dat in data[0]:
            new_data.append((dat[0] + addend, dat[1] + addend2))
        data[0] = new_data

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
            data[1] = args[1]
        elif isinstance(args[0], (int, float)) and isinstance(args[1], (tuple, list)):
            data[1] = args[0]
            data[2] = args[1]

def cleardisp(args):
    Drawer.values = [0] * len(Drawer.values)

def drawsprite(data, args):
    is_3D = len(data[0][0]) == 3
    size = data[1]
    position = data[2]
    if is_3D:
        prevline = data[0][0]
        for line in data[0]:
            x = position[0] + prevline[0] * size
            y = position[1] + prevline[1] * size
            z = position[2] + prevline[2] * size
            x2 = position[0] + line[0] * size
            y2 = position[1] + line[1] * size
            z2 = position[2] + line[2] * size
            Manager3D.draw_line_3d(x, y, z, x2, y2, z2)
            prevline = line
    else:
        prevline = data[0][0]
        for line in data[0]:
            x = position[0] + prevline[0] * size
            y = position[1] + prevline[1] * size
            x2 = position[0] + line[0] * size
            y2 = position[1] + line[1] * size
            Drawer.draw_line(x, y, x2, y2)
            prevline = line

def Display_Screen(args):
    print(Drawer.drawscreen(Drawer.values))

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
    if x:
        l[int(toapp)] = toval
        variables[x]["data"] = l
        variables[x]["type_data"] = l
def draw_kitty(args):
    """
    Renders Drawer's current buffer directly inside Kitty using the Kitty Graphics Protocol.
    Can be called inside Drawer.py or externally as Drawer.draw_kitty().
    """
    
    byte_data = bytearray()
    
    # Map default brightness levels (1-6) to grayscale RGB intensity if uncolored
    gray_levels = [0, 42, 85, 128, 170, 213, 255]

    for cell in Drawer.values:
        if isinstance(cell, tuple):
            brightness, (r, g, b) = cell
            if brightness == 0:
                byte_data.extend([0, 0, 0])
            else:
                byte_data.extend([int(r) & 0xFF, int(g) & 0xFF, int(b) & 0xFF])
        else:
            brightness = cell
            if 1 <= brightness <= 6:
                val = gray_levels[brightness]
                byte_data.extend([val, val, val])
            else:
                byte_data.extend([0, 0, 0])

    encoded = base64.b64encode(byte_data).decode("ascii")

    # Reposition terminal cursor to top-left corner
    sys.stdout.write("\033[H")
    
    # Kitty terminal graphics escape payload
    sys.stdout.write(f"\033_Ga=T,f=24,s={Drawer.size},v={Drawer.size};{encoded}\033\\")
    sys.stdout.flush()
def add_to_list(args):
    args2 = [parse_statement(arg) for arg in args]
    l = args2[0][0]
    toapp = args2[1][0]
    x = in_variables_index(args[0])
    if x:
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
        Drawer.switch_color(r,g,b)
    else:
        Drawer.switch_color()

def sin(args):
    return math.sin(parse_statement(args[0])[0])
def edit_screen_size(args):
    parsed = parse_statement(args[0])
    if parsed:
        Drawer.size = int(parsed[0])
        Drawer.values = [0] * (int(parsed[0]) ** 2)

def drawin(args):
    Drawer.drawscreen(Drawer.values)

def init(args):
    Drawer.init_window()

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

variables = [
    {
        "name": "square", 
        "type": "sprite", 
        "data": [[(-1, 1), (1, 1), (1, -1), (-1, -1), (-1, 1)], 1, [Drawer.middle, Drawer.middle], "square"],
        "properties": {
            "draw": drawsprite,
            "upd": updatespritedata,
            "updpos": updatepos,
            "three": 3,
        },
    },
]

def in_variables_index(name):
    for i, variable in enumerate(variables):
        if variable["name"] == name:
            return i
    return -1

def in_variables(name):
    for variable in variables:
        if variable["name"] == name:
            return variable
    return None

class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value

def call_user_function(func_name, raw_args):
    global user_functions, variables
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

    for param_name, arg_val in zip(params, parsed_args):
        p_type = "str" if isinstance(arg_val, str) else ("int" if isinstance(arg_val, int) else ("float" if isinstance(arg_val, float) else "str"))
        variables.append({
            "name": param_name,
            "type": p_type,
            "data": arg_val,
            "type_data": arg_val
        })

    return_val = None
    try:
        run_block(body)
    except ReturnValue as ret:
        return_val = ret.value
    finally:
        variables = old_variables

    return (return_val, ret_type)

def parse_statement(state):
    global CFuncs, user_functions
    if state is None:
        return ("", "str")
    state = str(state).strip()
    if not state:
        return ("", "str")

    STRING = re.match(r"^['\"](.*)['\"]$", state)
    INTEGER = re.match(r"(^[+-]?\d+)$", state)
    LIST = re.match(r"^[\{\(](.+)[\}\)]$", state) 
    BOOL = re.match(r"(^true|false$)",state)
    FLOAT = re.match(r"(^[+-]?[0-9]*\.[0-9]+|[0-9]+\.[0-9]*)$", state)
    CuFunc = re.match(r'^\*(.+?)\*\((.*)\)$', state)
    POSSIBLEINDENT = re.match(r"^(.+)\[(.+)\]$", state)


    if "." in state and not FLOAT:
        var_name = state.split(".")[0]
        v = in_variables(var_name)
        if v and "properties" in v:
            properti = state.split(".")[1]
            if properti in v["properties"]:
                prop = v["properties"][properti]
                if type(prop) == types.FunctionType:
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
                # Option A: Fallback to 0 if an uninitialized/invalid variable was passed
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
                        if type(l_val).__name__ == "list":
                            l_val = l_val[0]
                        res = l_val % r_val
                    res_type = "float" if isinstance(res, float) else "int"
                except Exception:
                    res = 0
                    res_type = "int"
                return (res, res_type)

    v = in_variables(state)
    if v is not None:
        val = v.get("type_data", v.get("data"))
        val_type = v.get("type", type(val).__name__)
        return (val, val_type)

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
        if bok == "true":
            return (True,"bool")
        else:
            return (False,"bool")
    if POSSIBLEINDENT:
        var = POSSIBLEINDENT.group(1)
        ind = POSSIBLEINDENT.group(2)
        var = parse_statement(var)
        if var:
            if var[1] == "list":
                return parse_statement(var[0][int(parse_statement(ind)[0])])
            elif var[1] == "str":
                return var[0][parse_statement(ind)[0]]
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

    if STRING:
        return (STRING.group(1), "str")

    
    return None

def execute_line(line,i):
    if line.startswith("return"):
        expr = line[6:].strip()
        val = parse_statement(expr)[0] if expr else None
        raise ReturnValue(val)

    Declare = re.match(r"(.+): (int|str|string|list|float|bool) (.+)", line)
    CustomFunc = re.match(r'^\*(.+?)\*\((.*)\)$', line)
    if Declare:
        var_name = Declare.group(1).strip()
        type_name = "str" if Declare.group(2) == "string" else Declare.group(2)
        parsed_val = parse_statement(Declare.group(3))
        
        if var_name.isidentifier() and parsed_val is not None:
            idx = in_variables_index(var_name)
            val = parsed_val[0]
            if idx != -1:
                variables[idx]["type_data"] = val
                variables[idx]["data"] = val
                variables[idx]["type"] = type_name
            else:
                variables.append(
                    {
                        "name": var_name,
                        "type": type_name,
                        "data": val,
                        "type_data": val
                    }
                )
    elif CustomFunc:
        func_name = CustomFunc.group(1)
        raw_args = CustomFunc.group(2).strip()
        args = [a.strip() for a in raw_args.split(",")] if raw_args else []
        if func_name in CFuncs:
            CFuncs[func_name](args)
        elif func_name in user_functions:
            call_user_function(func_name, args)
    else:
        if in_variables(line.split(".")[0]) is not None:
            x = in_variables(line.split(".")[0])
            if "." in line:
                properties = x["properties"]
                func_part = line.split(".")[1]
                
                if "(" in func_part and func_part.endswith(")"):
                    name = func_part[:func_part.index("(")]
                    args_raw = func_part[func_part.index("(")+1:-1]
                    
                    hello = []
                    for item in args_raw.split(","):
                        item = item.strip()
                        if not item: continue
                        
                        parsed = parse_statement(item)
                        if parsed is not None:
                            hello.append(parsed[0])
                        else:
                            raise ValueError(f"Could not parse argument '{item}': Not a literal or known variable.")
                    
                    properties[name](x["data"], hello)   
        else:
            if not parse_statement(line):
                raise NameError(f"Unknown Statement on line {i}: {line}")

def run_block(lines):
    i = 0
    while i < len(lines):
        line = lines[i]
        line = line.split("/-")[0].strip()
        
        func_match = re.match(r"^(int|str|string|list|float|bool|void)\s+([a-zA-Z_]\w*)\s*\((.*)\)\s*\[$", line)
        block_match = re.match(r"^(if|for|while|match)\s*\((.+)\)\s*\[$", line)
        one_lined = re.match(r"^(if)\s*\((.+?)\)\s*\[(.+?)\]$",line)
        
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
                for line in block_lines:
                    wow = re.match(r"case\s+(.+?)\s*\[\s*(.+?)\s*\]",line)
                    default = re.match(r"^default\s*\[\s*(.+)\s*\]$",line)
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
            execute_line(line,i)
        i += 1

def run_script(filename):
    with open(filename, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith('/-')]
    run_block(lines)

run_script("Ping_Pong.draw") # Put your .draw code here!
# VS
