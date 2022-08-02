import copy
import decimal
from re import A
from time import time
from PIL import ImageTk
import math
from enum import Enum
import random
from settings import *

class Blocks(Enum):
    AIR = -1
    GRASS = 0
    DIRT = 1
    STONE = 2
    BEDROCK = 3

class Entity:
    def __init__(self, x, y, dx = 0, dy = 0):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.gravityVal = 0.1

    def updateWrapper(self, app, *args):
        self.y -= self.dy
        self.gravity(app)
        self.checkForCollision(app)
        self.x += self.dx
        if app.func.goodGraphics:
            self.dx *= 0.6
        else:
            self.dx *= 0.7
        if abs(self.dx) < 0.005:
            self.dx = 0
        if hasattr(self, "update"):
            self.update(app, *args)
    
    def gravity(self, app):
        if app.func.goodGraphics:
            self.dy += self.gravityVal * 1.5
        else:
            self.dy += self.gravityVal

    def checkForCollision(self, app):
        blockLeft = getBlockFromCoords(app, math.floor(self.x) - 1, math.ceil(self.y))
        blockRight = getBlockFromCoords(app, math.ceil(self.x), math.ceil(self.y))
        blockTop = getBlockFromCoords(app, math.floor(self.x), int(self.y + 1))
        blockCenter = getBlockFromCoords(app, int(self.x), int(self.y))
        
        # Right Collision
        if 0 < self.dx <= 1:
            if blockRight and blockRight.solid:
                self.dx = 0
                self.x = blockRight.x - 0.9

        # Left Collision
        if -1 <= self.dx < 0:
            if blockLeft and blockLeft.solid:
                self.dx = 0
                self.x = blockLeft.x + 1.1
        
        # Top Collision
        if self.dy < 0 and blockTop and blockTop.solid:
            self.dy = 0
            self.y = blockTop.y - 1
        
        # Gravity Collision
        if isOnGround(app, self.x, self.y) and self.dy >= 0:
            self.dy = 0
            groundLeft = getGround(app, math.floor(self.x), self.y)
            groundRight = getGround(app, math.floor(self.x + 0.8), self.y)
            self.y = max(groundLeft, groundRight)

###############################################################################
# HELPER FUNCS

def almostEqual(d1, d2, epsilon=10**-7):  # helper-fn
    # note: use math.isclose() outside 15-112 with Python version 3.5 or later
    return (abs(d2 - d1) < epsilon)

def getBlockFromCoords(app, x, y):
    for chunk in app.game.loaded:
        if chunk.inChunk(app, x) and 0 <= y <= BUILD_HEIGHT and (x, y) in chunk.blocks:
            return chunk.blocks[(x, y)]
    return None

def isOnGround(app, x, y):
    groundLeft = getGround(app, math.floor(x), y)
    groundRight = getGround(app, math.floor(x + 0.8), y)
    if y - groundLeft <= 0.4 or y - groundRight <= 0.4:
        return True
    return False

def getCoordsFromPix(app, xPix, yPix):
    blockY = math.ceil(-(yPix - app.height * 0.6) / UNIT_WH) + app.player.y
    for chunk in app.game.loaded:
        for b in range(CHUNK_SIZE):
            if (b + chunk.x, blockY) in chunk.blocks:
                block = chunk.blocks[(b + chunk.x, blockY)]
                blockX = ((block.x - app.player.x) * UNIT_WH) + (app.width // 2)
                if blockX <= xPix and xPix < blockX + UNIT_WH:
                    return block.x, block.y
        
def getPixFromCoords(app, x, y):
    return getPixX(app, x), getPixY(app, y)

def getPixX(app, x):
    return ((x - app.player.x) * UNIT_WH) + (app.width // 2)

def getPixY(app, y):
    return (app.height * 0.6) + ((app.player.y - y) * UNIT_WH)

def getGround(app, x, y):
    for chunk in app.game.loaded:
        if chunk.inChunk(app, x):
            for r in range(math.ceil(y), -1, -1):
                if (x, r) in chunk.blocks and chunk.blocks[(x, r)].solid:
                    return chunk.blocks[(x, r)].y + 1
    return -1

def generateChunks(app):
    if min(app.game.loaded).index < min(app.game.chunks.values()).index + 2:
        app.game.generateChunk(app, False)
    if max(app.game.loaded).index > max(app.game.chunks.values()).index - 2:
        app.game.generateChunk(app, True)

def drawBlock(app, block, canvas):
    x, y = getPixFromCoords(app, block.x, block.y)

    if app._clearCanvas:

        if app.func.goodGraphics:
            image = getImage(app, block.type.name)
            if image != None:
                canvas.create_image(x, y, anchor="nw", image=image)
        else:
            if block.type.name != "AIR":
                canvas.create_rectangle(x, y, x + UNIT_WH, y + UNIT_WH,
                                    fill=block.color, width=0)

        if app.func.hovering and app.func.hovering == block:
            if not app.func.canInteract:
                outline = "#929292"
            else:
                outline = "#F4AC38"
            if app.func.holding:
                heldTime = time() - app.func.holding
                width = heldTime / 0.1 * 5
            else:
                width = 1
            app.func.hoveringRect = canvas.create_rectangle(x, y, x + UNIT_WH, y + UNIT_WH,
                                    outline=outline, width=width)

def moveBlock(app, block, canvas):
    x, y = getPixFromCoords(app, block.x, block.y)
    if block.type == Blocks.AIR:
        return
    image = block.image
    if image == None:
        return
    canvas.moveto(image, x, y)

def checkBackground(app):
    if min(app.game.bgX) > 0: # Left
            app.game.bgX = [0] + app.game.bgX
    if max(app.game.bgX) < app.width: # Right
            app.game.bgX = app.game.bgX + [max(app.game.bgX) + app.background.width()]

    newList = []
    for i in app.game.bgX: # Garbage Collector
        if i > - app.background.width():
            newList.append(i)
        if i < app.width:
            newList.append(i)
def roundHalfUp(d):  # helper-fn
    # Round to nearest with ties going away from zero.
    rounding = decimal.ROUND_HALF_UP
    # See other rounding options here:
    # https://docs.python.org/3/library/decimal.html#rounding-modes
    return int(decimal.Decimal(d).to_integral_value(rounding=rounding))

def getImage(app, name, resize = None):
    if name not in app.images:
        return None
    img = copy.copy(app.images[name])
    if resize:
        img = img.resize(resize)
    return ImageTk.PhotoImage(img)

def withinBounds(x1, y1, x2, y2, x, y):
    return x1 <= x <= x2 and y1 <= y <= y2

def generateTerrain(y1, y2, displace=1, length=0):
    if 2**(length + 1) >= CHUNK_SIZE:
        return [y1, y2]
    displacement = random.randint(0, displace)
    multiply = -1 if random.randint(0, 1) else 1
    midpoint = int(((y1 + y2) / 2) + displacement * multiply)
    length += 1
    return (generateTerrain(y1, midpoint, int(displace * 0.5), length) +
        generateTerrain(midpoint, y2, int(displace * 0.5), length))
