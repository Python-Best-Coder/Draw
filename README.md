# Draw
A typical ascii drawer, using the most basic modules, including os,time,colorama, and math.


# How use DrawPi
DRAWPI PROGRAMMING LANGUAGE GUIDE

Welcome to the official documentation and language reference for Drawpi, a lightweight interpreted language designed for 2D/3D graphics rendering, sprite manipulation, and interactive execution.


TABLE OF CONTENTS

1. Program Structure & Syntax
2. Data Types & Variables
3. Operators & Expressions
4. Control Flow
   - If Statements
   - Loops
5. Functions
   - Function Definition Syntax
   - Function Examples
6. Built-in Commands (CFuncs)
7. Objects & Sprites
8. Complete Sample Program (Test.draw)


### 1. PROGRAM STRUCTURE & SYNTAX

Drawpi programs are saved in files with a .draw extension. Based on general knowledge of interpreter mechanics, files are executed line-by-line or block-by-block.

Comments:
Single-line comments begin with /-. Everything following /- on that line is ignored by the parser.
```
/- This is a comment in Drawpi
x: int 10 /- Inline comments are also supported
```

### 2. DATA TYPES & VARIABLES

Variables are declared with explicit type annotations using the following format:

<variable_name>: <type> <value>

## Supported Data Types:

Type            Description                            Example
int             Signed integers                        x: int 42
float           Floating-point numbers                 pi: float 3.14159
str / string    Text literals wrapped in quotes        msg: string "Hello World"
bool            Boolean values (true or false)         flag: bool true
list            Enclosed lists using () or {}          coords: list (10, 20, 30)

Examples:
```
score: int 100
speed: float 2.5
player_name: string "Marcus"
is_active: bool true
points: list (1, 2, 3)
```

### 3. OPERATORS & EXPRESSIONS

Drawpi supports arithmetic, comparison, and logical operators across variable assignments, loop conditions, and expressions.

Operators Summary:

Category        Operators              Description
Arithmetic      +, -, *, /             Standard mathematical calculations
Comparison      ==, !=, <, >, <=, >=   Conditional comparison evaluation
Logical         and, or, not           Boolean logic chaining

Examples:
```
x: int 5 + 10 * 2
is_valid: bool x > 15 and not false
```

### 4. CONTROL FLOW

Control blocks evaluate expressions enclosed in parentheses () and scope statement blocks using square brackets [ and ].

If Statements:
```
if (x > 5) [
    *pout*("x is greater than 5")
]
```
## Loops:

# for Loops
A for loop accepts an integer count or an iterable list:
```
/- Iterates 5 times
for (5) [
    *pout*("Loop iteration")
]
```
# while Loops
A while loop continues execution as long as the conditional expression evaluates to true:
```
count: int 0
while (count < 3) [
    *pout*(count)
    count: int count + 1
]
```

### 5. FUNCTIONS

Custom user functions are defined with explicit return types, parameter lists, and executable block scopes.

Function Definition Syntax:
```
<return_type> <function_name> (param1, param2, ...) [
    /- Function body
    return <value>
]
```
Function Examples:

Void / Action Function:
```void greet (name) [
    *pout*("Hello " + name)
]

*greet*("Marcus")
```
Value-Returning Function:
```
int add (x, y) [
    return x + y
]

result: int *add*(10, 20)
*pout*(result)
```

### 6. BUILT-IN COMMANDS (CFuncs)

Drawpi includes built-in system routines that are called using the asterisk-wrapped syntax *command_name*(args):

Command         Signature                      Description
pout            *pout*(value)                  Prints a value or expression result to stdout.
display         *display*()                    Standard terminal display output call.
wait            *wait*(ms)                     Delays execution by the specified milliseconds.
clr             *clr*()                        Clears the host console/terminal screen.
clrd            *clrd*()                       Clears the display memory buffer in Drawer.
clrds           *clrds*()                      Clears both the terminal screen and display buffer.
editsize        *editsize*(size)               Sets screen size and reinitializes screen buffer array.
drlin           *drlin*(x1, y1, x2, y2, [b])   Draws a line segment with optional brightness b.
inp             *inp*()                        Queries current key state via keyboard hook.
updspec         *updspec*()                    Updates screen specifications inside Drawer.


### 7. OBJECTS & SPRITES

Objects in Drawpi (such as the default square sprite variable) encapsulate instance data alongside member methods accessible via dot notation:

/- Offset sprite coordinates
`square.updpos(10, 5)`

/- Update sprite size and anchor position
`square.upd(2, (100, 100))`

/- Render sprite lines to current display context
`square.draw()`


### 8. COMPLETE SAMPLE PROGRAM (Test.draw)
```
/- Set display resolution
*editsize*(32)

/- Define custom helper function
int calculate_offset (val, factor) [
    return val * factor
]

offset: int *calculate_offset*(2, 3)
*pout*("Calculated offset:")
*pout*(offset)

/- Main loop
running: bool true
while (running) [
    key: str *inp*()
    
    if (key == "q") [
        running: bool false
    ]
    
    *clrd*()
    square.updpos(1, 0)
    square.draw()
    *display*()
    *wait*(50)
]

*pout*("Program terminated successfully.")
```
