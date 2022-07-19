import json
import math
from pprint import pprint
import tkinter

from PIL import Image,ImageTk
from cmu_112_graphics import *
import random
from enum import Enum
import decimal
import os
from assets.colors import colors

###############################################################################
# CLASSES
class Blocks(Enum):
    GRASS = 0
    DIRT = 1
    STONE = 2

class Block:
    def __init__(self, x, y, block: Blocks, chunk):
        self.x = x
        self.y = y
        self.type = block
        self.chunk = chunk

class Chunk:
    def __init__(self, app, x, chunkI):
        self.blocks = {}
        self.x = x
        for i in range(app.CHUNK_SIZE):
            # TODO: random ground level
            row_grass_level = app.GRASS_LEVEL + random.randint(0, 1)
            row_dirt_level = app.DIRT_LEVEL + random.randint(0, 1)
            for r in range(app.GROUND_LEVEL, 0, -1):
                if r > row_grass_level:
                    self.blocks[(x+i, r)] = Block(x+i, r, Blocks.GRASS, chunkI)
                elif r > row_dirt_level:
                    self.blocks[(x+i, r)] = Block(x+i, r, Blocks.DIRT, chunkI)
                else:
                    self.blocks[(x+i, r)] = Block(x+i, r, Blocks.STONE, chunkI)
    def getRange(self):
        return self.x, self.x + self.CHUNK_SIZE
    def inChunk(self, app, x):
        return self.x <= x and x < self.x + app.CHUNK_SIZE
class Game:
    def __init__(self, app):
        self.chunks = {}
        self.time = 0
        self.bgX = [0, app.background.width(), -app.background.width()]
        for i in range(20):
            chunkX = (i - 10) * app.CHUNK_SIZE + 2
            self.chunks[i] = Chunk(app, chunkX, i)

    def generateChunk(self, app, right):
        if right:
            highest = max(self.chunks)
            chunk = Chunk(app, self.chunks[highest].x + app.CHUNK_SIZE, len(self.chunks))
            self.chunks[len(self.chunks)] = chunk
        else:
            lowest = min(self.chunks)
            chunk = Chunk(app, self.chunks[lowest].x - app.CHUNK_SIZE, lowest - 1)
            self.chunks[lowest - 1] = chunk
            
    def getChunk(self, app, i):
        if i in self.chunks:
            return self.chunks[i]
        else:
            while i not in self.chunks:
                self.generateChunk(app, i > 10)
            return self.chunks[i]
class Entity:
    def __init__(self, app):
        self.x = 0
        self.y = app.GROUND_LEVEL + 1
        self.falling = 0

class Player(Entity):
    def __init__(self, app):
        self.chunk = 9
        self.x = 0
        self.y = app.GROUND_LEVEL + 1
        self.inventory = []
        self.falling = 0
        self.orient = 1
        self.health = 20
        self.image = Image.open("assets/boris.png").resize((app.UNIT_WH, app.UNIT_WH))
    
    def getSprite(self):
        image = self.image.copy()
        if self.orient == -1:
            image = image.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        return ImageTk.PhotoImage(image)

class Item(Entity):
    def __init__(self, app, name, x, y, props = None, count = 1):
        self.name = name
        self.x = x
        self.y = y
        self.count = count
        self.props = props
        

class Functionality:
    def __init__(self, app):
        self.mouseX = 0
        self.mouseY = 0
        self.hovering = None
        self.debug = True
        
        
###############################################################################
# HELPER FUNCS

def almostEqual(d1, d2, epsilon=10**-7):  # helper-fn
    # note: use math.isclose() outside 15-112 with Python version 3.5 or later
    return (abs(d2 - d1) < epsilon)

def getBlockFromCoords(app, x, y):
    for chunk_i in app.game.chunks:
        chunk = app.game.getChunk(app, chunk_i)
        if (x, y) in chunk.blocks:
            return chunk.blocks[(x, y)]
    return None

def isOnGround(app):
    playerY = app.player.y
    y = (app.height - playerY * app.UNIT_WH) - 1
    groundY = (app.height - getGround(app, roundHalfUp(app.player.x)) * app.UNIT_WH) - 1
    if y - app.player.falling + 0.3 > groundY:
        return True
    return False

def getCoordsFromPix(app, xPix, yPix):
    # divide width by chunk size, add 2 chunks for margin
    chunksOnScreen = int(app.width / (app.CHUNK_SIZE * app.UNIT_WH)) + 2
    # the index of the first chunk on the screen
    startChunkIndex = int(max(0, app.player.chunk - (chunksOnScreen / 2))) + 1
    blockY = ((app.height - yPix) // app.UNIT_WH) + 1
    for chunk_i in range(startChunkIndex,startChunkIndex + chunksOnScreen):
        chunk = app.game.getChunk(app, chunk_i)
        for b in range(app.CHUNK_SIZE):
            if (b + chunk.x, blockY) in chunk.blocks:
                block = chunk.blocks[(b + chunk.x, blockY)]
                blockX = ((block.x - app.player.x) * app.UNIT_WH) + (app.width // 2)
                if blockX <= xPix and xPix < blockX + app.UNIT_WH:
                    return block.x, block.y
        
def getPixFromCoords(app, x, y):
    return (x * app.UNIT_WH) + (app.width // 2) + (app.UNIT_WH // 2), \
        (app.height - y * app.UNIT_WH) + (app.UNIT_WH // 2)

def getGround(app, x):
    for chunk_i in app.game.chunks:
        chunk = app.game.getChunk(app, chunk_i)
        if chunk.x < x and x < chunk.x + app.CHUNK_SIZE:
            for r in range(app.BUILD_HEIGHT, -1, -1):
                if (x, r) in chunk.blocks:
                    return chunk.blocks[(x, r)].y + 1
    return app.GROUND_LEVEL + 1

def generateChunks(app):
    chunksOnScreen = int(app.width / (app.CHUNK_SIZE * app.UNIT_WH)) + 2
    startChunkIndex = int(max(0, app.player.chunk - (chunksOnScreen / 2))) + 1
    if startChunkIndex + chunksOnScreen + 5 > len(app.game.chunks):
        for i in range(len(app.game.chunks), startChunkIndex + chunksOnScreen):
            app.game.generateChunk(app, True)
    elif startChunkIndex - 5 < min(app.game.chunks):
        for i in range(startChunkIndex - 5, 0):
            app.game.generateChunk(app, False)
    
def checkBackground(app):
    if min(app.game.bgX) > 0:
            app.game.bgX = [0] + app.game.bgX
    if max(app.game.bgX) < app.width:
            app.game.bgX = app.game.bgX + [max(app.game.bgX) + app.background.width()]
def roundHalfUp(d):  # helper-fn
    # Round to nearest with ties going away from zero.
    rounding = decimal.ROUND_HALF_UP
    # See other rounding options here:
    # https://docs.python.org/3/library/decimal.html#rounding-modes
    return int(decimal.Decimal(d).to_integral_value(rounding=rounding))

def getImage(app, name):
    return app.images[name]

###############################################################################
# MVC

def appStarted(app):
    app.GRASS_LEVEL = 8
    app.DIRT_LEVEL = 4
    app.UNIT_WH = 18
    app.GROUND_LEVEL = int((app.height / 2) - 40) // app.UNIT_WH
    app.CHUNK_SIZE = 8
    app.BUILD_HEIGHT = 64
    app.images = {}
    app.background = ImageTk.PhotoImage(Image.open("assets/background.png"))
    for f in os.listdir("assets"):
        if not f.endswith(".png"):
            continue
        app.images[f[:-4]] = ImageTk.PhotoImage(Image.open("assets/" + f).resize((app.UNIT_WH, app.UNIT_WH)))
    app.game = Game(app)
    app.player = Player(app)
    app.func = Functionality(app)
    checkBackground(app)

def keyPressed(app, event):
    """
    PLAYER
    """
    if event.key == "Up" and app.player.falling < 0.05:
        app.player.falling = 0.01
    ground = getGround(app, roundHalfUp(app.player.x)) - 1
    if event.key == "Left":
        app.player.orient = -1
        app.player.x = round(app.player.x - 0.5, 5)
        app.player.chunk = getBlockFromCoords(app, int(app.player.x), ground).chunk
        app.game.bgX = [app.game.bgX[i] + 2 for i in range(len(app.game.bgX))]
    elif event.key == "Right":
        app.player.orient = 1
        app.player.x = round(app.player.x + 0.5, 5)
        app.player.chunk = getBlockFromCoords(app, int(app.player.x), ground).chunk
        app.game.bgX = [app.game.bgX[i] - 2 for i in range(len(app.game.bgX))]
    checkBackground(app)
    """
    FUNC
    """
    if event.key == "d":
        app.func.debug = not app.func.debug
    """
    GAME
    """
    generateChunks(app)

def sizeChanged(app):
    generateChunks(app)
    checkBackground(app)

def mouseMoved(app, event):
    app.func.mouseX = event.x
    app.func.mouseY = event.y
    coords = getCoordsFromPix(app, event.x, event.y)
    if coords:
        app.func.hovering = getBlockFromCoords(app, coords[0], coords[1])

def mousePressed(app, event):
    pass

def drawChunk(app, canvas: tkinter.Canvas, chunk: Chunk):
    for r in range(chunk.x, chunk.x + app.CHUNK_SIZE):
        for b in range(1, app.GROUND_LEVEL + 1):
            block = chunk.blocks[(r, b)]
            x = ((block.x - app.player.x) * app.UNIT_WH) + (app.width // 2)
            y = (app.height) - (block.y * app.UNIT_WH)
            canvas.create_image(x, y, anchor="nw", image=getImage(app, block.type.name))
            if r == chunk.x and app.func.debug:
                canvas.create_rectangle(x, 0, x + (app.CHUNK_SIZE * app.UNIT_WH), app.height,
                            outline=("red" if chunk.x == app.game.getChunk(app, app.player.chunk).x else "black"))
    if app.func.hovering:
        block = app.func.hovering
        x = ((block.x - app.player.x) * app.UNIT_WH) + (app.width // 2)
        y = (app.height) - (block.y * app.UNIT_WH)
        canvas.create_rectangle(x, y,
                                x + app.UNIT_WH, y + app.UNIT_WH, outline="#00ff00")

def drawGame(app, canvas: tkinter.Canvas):
    canvas.create_rectangle(0, 0, app.width, app.height,
                            fill=colors[int(app.game.time)])
    chunksOnScreen = int(app.width / (app.CHUNK_SIZE * app.UNIT_WH)) + 3
    startChunkIndex = int(app.player.chunk - (chunksOnScreen / 2)) + 1
    for bgX in app.game.bgX:
        canvas.create_image(bgX, app.height - ((app.GROUND_LEVEL + 4) * app.UNIT_WH), anchor="e", image=app.background)
    for chunk_i in range(startChunkIndex, chunksOnScreen + startChunkIndex):
        drawChunk(app, canvas, app.game.getChunk(app, chunk_i))

def drawPlayer(app, canvas: tkinter.Canvas):
    _, y = getPixFromCoords(app, app.player.x, app.player.y)
    x = app.width / 2
    canvas.create_image(x, y + (app.UNIT_WH / 2), image=app.player.getSprite(), anchor="sw")

def drawDebug(app, canvas: tkinter.Canvas):
    blockCoords = getCoordsFromPix(app, app.func.mouseX, app.func.mouseY)
    orient = '>' if app.player.orient == 1 else '<'
    canvas.create_text(5, 10, text=f"G: {int(app.game.time)}", anchor="nw")
    canvas.create_text(5, 30,
                       text=f'P: ({app.player.x}, {app.player.y}) {app.player.chunk} {orient}',
                       fill="#000000", anchor="w")
    if blockCoords:
        block = getBlockFromCoords(app, blockCoords[0], blockCoords[1])
        canvas.create_text(5, 50,
                        text=f'M: ({app.func.mouseX}, {app.func.mouseY})',
                        fill="#000000", anchor="w")
        if block:
            canvas.create_text(5, 70,
                       text=f'B: ({block.x}, {block.y}) {block.type.name} {block.chunk}',
                       fill="#000000", anchor="w")
def redrawAll(app, canvas:tkinter.Canvas):
    drawGame(app, canvas)
    drawPlayer(app, canvas)
    if app.func.debug:
        drawDebug(app, canvas)

def timerFired(app):
    """
    PLAYER
    """
    if app.player.falling != 0:
        app.player.y = round(app.player.y - (app.player.falling - 0.15), 5)
        app.player.falling += 0.01
        if isOnGround(app):
            app.player.y = getGround(app, roundHalfUp(app.player.x))
            app.player.falling = 0
    """
    GAME
    """
    app.game.time = round((app.game.time + 0.01) % 23, 2)

def main():
    runApp(width=500, height=500, title="Terraria")
    
if __name__ == "__main__":
    main()