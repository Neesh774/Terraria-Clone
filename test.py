import random

def makeMaze(maze):
    valid = checkMazeValid(maze)
    if valid == 1:
        return maze
    intersection = (random.randint(1, len(maze[0]) - 2), random.randint(1, len(maze) - 2))
    tries = 0
    while checkChamber(maze, intersection[0], intersection[1]):
        intersection = (random.randint(1, len(maze[0]) - 2), random.randint(1, len(maze) - 2))
        tries += 1
        if tries > 100:
            return maze
    wallWithoutHole = random.randint(0, 3)
    maze[intersection[0]][intersection[1]] = 1
    for i in range(0, 4):
        dx, dy = 0, 0
        if i == 0:
            dx = -1
        elif i == 1:
            dy = 1
        elif i == 2:
            dx = 1
        elif i == 3:
            dy = -1
        maze = makeWall(maze, intersection[0] + dx, intersection[1] + dy, i, i != wallWithoutHole)
    return makeMaze(maze)

def makeWall(maze, x, y, wall, hasHole):
    if wall == 0: # top
        wallY = y
        if hasHole:
            hole = random.randint(0, x)
            while x >= 0 and maze[x][wallY] != 1:
                maze[x][wallY] = 1 if x != hole else 0
                x -= 1
        else:
            while x >= 0 and maze[x][wallY] != 1:
                maze[x][wallY] = 1
                x -= 1
    
    elif wall == 1: # right
        wallX = x
        if hasHole:
            hole = random.randint(y, len(maze) - 1)
            while y < len(maze) and maze[wallX][y] != 1:
                maze[wallX][y] = 1 if y != hole else 0
                y += 1
        else:
            while y < len(maze) and maze[wallX][y] != 1:
                maze[wallX][y] = 1
                y += 1
    
    elif wall == 2: # bottom
        wallY = y
        if hasHole:
            hole = random.randint(x, len(maze[0]) - 1)
            while x < len(maze[0]) and maze[x][wallY] != 1:
                maze[x][wallY] = 1 if x != hole else 0
                x += 1
        else:
            while x < len(maze[0]) and maze[x][wallY] != 1:
                maze[x][wallY] = 1
                x += 1
    
    elif wall == 3: # left
        wallX = x
        if hasHole:
            hole = random.randint(0, y)
            while y >= 0 and maze[wallX][y] != 1:
                maze[wallX][y] = 1 if y != hole else 0
                y -= 1
        else:
            while y >= 0 and maze[wallX][y] != 1:
                maze[wallX][y] = 1
                y -= 1
    return maze

def checkChamber(maze, x, y):
    numWalls = 0
    for i in range(x - 1, x + 2):
        for j in range(y - 1, y + 2):
            if 0 < i < len(maze) and 0 < j < len(maze[0]):
                numWalls += maze[i][j]
    return numWalls

def checkMazeValid(maze):
    for i in range(0, len(maze)):
        for j in range(0, len(maze[0])):
            if checkChamber(maze, i, j) == 0:
                return 0
    return 1

def printMaze(maze):
    for i in range(0, len(maze) + 1):
        print("__", end="")
    print()
    for i in range(0, len(maze)):
        print("|", end="")
        for j in range(0, len(maze[0])):
            if maze[i][j] == 1:
                print("[]", end="")
            elif maze[i][j] == 0:
                print("  ", end="")
        print("|")
    for i in range(0, len(maze) + 1):
        print("--", end="")
    print()

def emptyMaze(size):
    return [[0 for i in range(0, size)] for j in range(0, size)]

printMaze(makeMaze(emptyMaze(10)))