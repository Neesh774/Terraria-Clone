import copy
import decimal
from time import time
from PIL import ImageTk
import math
from enum import Enum

class Blocks(Enum):
    AIR = -1
    GRASS = 0
    DIRT = 1
    STONE = 2
    BEDROCK = 3

class Entity:
    def __init__(self, app):
        self.x = 0
        self.y = app.GROUND_LEVEL + 1
        self.falling = 0

###############################################################################
# HELPER FUNCS

def almostEqual(d1, d2, epsilon=10**-7):  # helper-fn
    # note: use math.isclose() outside 15-112 with Python version 3.5 or later
    return (abs(d2 - d1) < epsilon)

def getBlockFromCoords(app, x, y):
    for chunk in app.game.loaded:
        if chunk.inChunk(app, x) and 0 <= y <= app.BUILD_HEIGHT and (x, y) in chunk.blocks:
            return chunk.blocks[(x, y)]
    return None

def isOnGround(app):
    groundLeft = getGround(app, math.floor(app.player.x))
    groundRight = getGround(app, math.floor(app.player.x + 0.8))
    y = app.player.y
    if y - groundLeft <= 0.4 or y - groundRight <= 0.4:
        return True
    return False

def getCoordsFromPix(app, xPix, yPix):
    blockY = math.ceil(-(yPix - app.height * 0.6) / app.UNIT_WH) + app.player.y
    for chunk in app.game.loaded:
        for b in range(app.CHUNK_SIZE):
            if (b + chunk.x, blockY) in chunk.blocks:
                block = chunk.blocks[(b + chunk.x, blockY)]
                blockX = ((block.x - app.player.x) * app.UNIT_WH) + (app.width // 2)
                if blockX <= xPix and xPix < blockX + app.UNIT_WH:
                    return block.x, block.y
        
def getPixFromCoords(app, x, y):
    return getPixX(app, x), getPixY(app, y)

def getPixX(app, x):
    return ((x - app.player.x) * app.UNIT_WH) + (app.width // 2)

def getPixY(app, y):
    return (app.height * 0.6) + ((app.player.y - y) * app.UNIT_WH)

def getGround(app, x):
    for chunk in app.game.loaded:
        if chunk.inChunk(app, x):
            for r in range(math.ceil(app.player.y), -1, -1):
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
        image = getImage(app, block.type.name)
        if image != None:
            canvas.create_image(x, y, anchor="nw", image=image)
        
        if app.func.hovering and app.func.hovering == block:
            if not app.func.canInteract:
                outline = "#929292"
            else:
                outline = "#F4AC38"
            app.func.hoveringRect = canvas.create_rectangle(x, y, x + app.UNIT_WH, y + app.UNIT_WH,
                                    outline=outline)

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

def getImage(app, name):
    if name not in app.images:
        return None
    img = copy.copy(app.images[name])
    return ImageTk.PhotoImage(img)