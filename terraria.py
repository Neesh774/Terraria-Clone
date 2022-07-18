import math
import tkinter
from cmu_112_graphics import *
import random
from enum import Enum
import decimal

def almostEqual(d1, d2, epsilon=10**-7):  # helper-fn
    # note: use math.isclose() outside 15-112 with Python version 3.5 or later
    return (abs(d2 - d1) < epsilon)

def getBlockFromCoords(app, x, y):
    for chunk in app.game.chunks:
        if (x, y) in chunk.blocks:
            return chunk.blocks[(x, y)]
    return None

def getCoordsFromPix(app, x, y):
    # divide width by chunk size, add 2 chunks for margin
    chunksOnScreen = int(app.width / (app.CHUNK_SIZE * app.UNIT_WH)) + 2
    # the index of the first chunk on the screen
    startChunkIndex = int(max(0, app.player.chunk - (chunksOnScreen / 2)))
    blockY = ((app.height - y) // app.UNIT_WH) + 1
    for i, chunk_i in enumerate(range(startChunkIndex, chunksOnScreen + startChunkIndex)):
        chunk = app.game.chunks[chunk_i]
        for r in range(chunk.x, chunk.x + app.CHUNK_SIZE):
            if r == (x - app.width / 2) // app.UNIT_WH:
                return (r, blockY)

def getPixFromCoords(app, x, y):
    return (x * app.UNIT_WH) + (app.width // 2), (app.height) - (y * app.UNIT_WH)
            

def roundHalfUp(d):  # helper-fn
    # Round to nearest with ties going away from zero.
    rounding = decimal.ROUND_HALF_UP
    # See other rounding options here:
    # https://docs.python.org/3/library/decimal.html#rounding-modes
    return int(decimal.Decimal(d).to_integral_value(rounding=rounding))

class Blocks(Enum):
    GRASS = 0
    DIRT = 1
    STONE = 2

class Block:
    def __init__(self, x, y, block: Blocks):
        self.x = x
        self.y = y
        self.type = block

class Chunk:
    def __init__(self, app, x):
        self.blocks = {}
        self.x = x
        for i in range(app.CHUNK_SIZE):
            # TODO: random ground level
            row_grass_level = app.GRASS_LEVEL + random.randint(0, 1)
            row_dirt_level = app.DIRT_LEVEL + random.randint(0, 1)
            for r in range(app.GROUND_LEVEL, 0, -1):
                if r > row_grass_level:
                    self.blocks[(x+i, r)] = Block(x+i, r, Blocks.GRASS)
                elif r > row_dirt_level:
                    self.blocks[(x+i, r)] = Block(x+i, r, Blocks.DIRT)
                else:
                    self.blocks[(x+i, r)] = Block(x+i, r, Blocks.STONE)
class Game:
    def __init__(self, app):
        self.chunks = []
        for i in range(20):
            chunkX = (i - 10) * app.CHUNK_SIZE + 2
            self.chunks.append(Chunk(app, chunkX))

class Player:
    def __init__(self, app):
        self.y = app.GROUND_LEVEL - app.UNIT_WH
        self.chunk = 10
        self.x = 0
        self.y = 1
        self.inventory = []
        self.falling = 0

class Functionality:
    def __init__(self, app):
        self.mouseX = 0
        self.mouseY = 0
        self.hovering = None

def appStarted(app):
    app.GRASS_LEVEL = 8
    app.DIRT_LEVEL = 4
    app.UNIT_WH = 18
    app.GROUND_LEVEL = int((app.height / 2) - 40) // app.UNIT_WH
    app.CHUNK_SIZE = 8
    app.game = Game(app)
    app.player = Player(app)
    app.func = Functionality(app)

def keyPressed(app, event):
    """
    PLAYER
    """
    if event.key == "Space" and app.player.falling == 0:
        app.player.falling = 0.05
    pass

def mouseMoved(app, event):
    app.func.mouseX = event.x
    app.func.mouseY = event.y
    coords = getCoordsFromPix(app, event.x, event.y)
    if coords:
        app.func.hovering = getBlockFromCoords(app, coords[0], coords[1])

def mousePressed(app, event):
    pass

def drawChunk(app, canvas: tkinter.Canvas, chunk: Chunk):
    def getBlockFill(block: Block):
        if block.type == Blocks.GRASS:
                fill = "#2AA52A"
        elif block.type == Blocks.DIRT:
            fill = "#7B5434"
        elif block.type == Blocks.STONE:
            fill = "#A2A2A2"
        return fill
    for r in range(chunk.x, chunk.x + app.CHUNK_SIZE):
        for b in range(1, app.GROUND_LEVEL + 1):
            fill = ""
            block = chunk.blocks[(r, b)]
            x = (block.x * app.UNIT_WH) + (app.width // 2)
            y = (app.height) - (block.y * app.UNIT_WH)
            canvas.create_rectangle(x, y,
                                    x + app.UNIT_WH, y + app.UNIT_WH,
                                    fill=getBlockFill(block))
    if app.func.hovering:
        block = app.func.hovering
        x = (block.x * app.UNIT_WH) + (app.width // 2)
        y = (app.height) - (block.y * app.UNIT_WH)
        canvas.create_rectangle(x, y,
                                x + app.UNIT_WH, y + app.UNIT_WH,
                                fill=getBlockFill(block), outline="#00ff00")

def drawGame(app, canvas: tkinter.Canvas):
    chunksOnScreen = int(app.width / (app.CHUNK_SIZE * app.UNIT_WH)) + 2
    startChunkIndex = int(max(0, app.player.chunk - (chunksOnScreen / 2)))
    for chunk_i in range(startChunkIndex, chunksOnScreen + startChunkIndex):
        drawChunk(app, canvas, app.game.chunks[chunk_i])

def drawPlayer(app, canvas: tkinter.Canvas):
    hcent = app.width / 2
    canvas.create_oval(hcent - 5, app.player.y, hcent + 5, app.player.y + app.UNIT_WH, fill="#00ff00")

def redrawAll(app, canvas:tkinter.Canvas):
    drawGame(app, canvas)
    drawPlayer(app, canvas)
    block = getCoordsFromPix(app, app.func.mouseX, app.func.mouseY)
    if block:
        canvas.create_text(40, 20,
                        text=f'({block[0]}, {block[1]})', fill="#000000")

def timerFired(app):
    """
    PLAYER
    """
    if app.player.falling != 0:
        app.player.y += (((app.player.falling - 1)**2) - 1) * 2
        app.player.falling = app.player.falling + 0.05
        if almostEqual(app.player.falling, 3):
            app.player.falling = 0
    pass

def main():
    runApp(width=500, height=500)
    
if __name__ == "__main__":
    main()