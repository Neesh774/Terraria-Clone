import copy
import decimal

import math
from enum import Enum
import random
from settings import *
from assets.colors import colors
import numpy as np

from pygame.key import *
from pygame.locals import *
import pygame


class Blocks(Enum):
    AIR = -1
    GRASS = 0
    DIRT = 1
    STONE = 2
    BEDROCK = 3
    LOG = 4
    PLANKS = 5
    PLATFORM = 6
    WALL = 7
    
class Entity(pygame.sprite.Sprite):
    def __init__(self, x, y, dx = 0, dy = 0):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.gravityVal = 0.05
        self.suffocationDamage = False
        self.suffocationDelay = -1

    def update(self, app, *args):
        self.y -= self.dy
        self.gravity(app)
        self.checkForCollision(app)
        self.x += self.dx
        self.dx *= 0.7
        if abs(self.dx) < 0.005:
            self.dx = 0
        if hasattr(self, "tick"):
            self.tick(app, *args)

        self.rect.x = getPixX(app, self.x)
        if hasattr(self, "width"):
            self.rect.x -= self.width / 2
        self.rect.y = getPixY(app, self.y)
        if hasattr(self, "height"):
            self.rect.y -= self.height / 2

    def gravity(self, app):
        self.dy += self.gravityVal

    def checkForCollision(self, app):
        blockLeft = getBlockFromCoords(app, math.floor(self.x) - 1, math.ceil(self.y))
        blockRight = getBlockFromCoords(app, math.ceil(self.x), math.ceil(self.y))
        blockTopLeft = getBlockFromCoords(app, math.floor(self.x), math.floor(self.y + 1))
        blockTopRight = getBlockFromCoords(app, math.ceil(self.x), math.floor(self.y + 1))
        blockBelow = getBlockFromCoords(app, roundHalfUp(self.x), math.floor(self.y) - 1)
        if blockTopLeft and blockTopLeft.solid:
            blockTop = blockTopLeft
        elif blockTopRight and blockTopRight.solid:
            blockTop = blockTopRight
        else:
            blockTop = None
        
        onGround = isOnGround(app, self.x, self.y - self.dy)
        
        # Right Collision
        if 0 < self.dx:
            
            topBlock = blockTopLeft and blockTopLeft.solid
            diagBlock = getBlockFromCoords(app, math.ceil(self.x), math.ceil(self.y) + 1)
            freeDiagBlock = not diagBlock or not diagBlock.solid
            sneak = self.sneak if hasattr(self, "sneak") else False
            if (blockRight and
                blockRight.solid and
                not topBlock and
                freeDiagBlock and
                onGround and
                not sneak):
                self.x = blockRight.x
                self.y = blockRight.y + 1
                self.dx = 0.01
            elif blockRight and blockRight.solid:
                self.dx = 0
                self.x = blockRight.x - 0.9

        # Left Collision
        elif self.dx < 0:
            
            topBlock = blockTop and blockTop.solid
            diagBlock = getBlockFromCoords(app, math.floor(self.x) - 1, math.ceil(self.y) + 1)
            freeDiagBlock = not diagBlock or not diagBlock.solid
            sneak = self.sneak if hasattr(self, "sneak") else False
            if (blockLeft and blockLeft.solid and not topBlock
                and freeDiagBlock and onGround and not sneak):
                self.x = blockLeft.x + 1
                self.y = blockLeft.y + 1
                self.dx = -0.01
            elif blockLeft and blockLeft.solid:
                self.dx = 0
                self.x = blockLeft.x + 1.1

        # Gravity Collision
        if isOnGround(app, self.x, self.y) and self.dy > 0:
            onGround = True
            self.dy = 0
            groundLeft = getGround(app, math.floor(self.x), self.y)
            groundRight = getGround(app, math.floor(self.x + 0.8), self.y)
            self.y = max(groundLeft, groundRight)
        
        # Top Collision
        if self.dy != 0 and blockTop and blockTop.solid == 1:
            if blockTopLeft:
                leftOverlap = hasOverlap(
                    (blockTopLeft.x, blockTopLeft.y,
                        blockTopLeft.x + 1, blockTopLeft.y + 1),
                    (self.x, self.y - self.dy, self.x + 0.8, self.y - self.dy + 0.8)
                )
            else:
                leftOverlap = False
            if blockTopRight:
                rightOverlap = hasOverlap(
                    (blockTopRight.x, blockTopRight.y,
                        blockTopRight.x + 1, blockTopRight.y + 1),
                    (self.x, self.y - self.dy, self.x + 0.8, self.y - self.dy + 0.8)
                )
            else:
                rightOverlap = False
            if leftOverlap and blockTopLeft.solid == 1:
                self.dy = 0
                self.y = blockTopLeft.y - 1
            if rightOverlap and blockTopRight.solid == 1:
                self.dy = 0
                self.y = blockTopRight.y - 1

###############################################################################
# HELPER FUNCS

def almostEqual(d1, d2, epsilon=10**-7):  # helper-fn
    # note: use math.isclose() outside 15-112 with Python version 3.5 or later
    return (abs(d2 - d1) < epsilon)

def getBlockFromCoords(app, x, y):
    for chunk in app.game.loaded:
        if chunk.inChunk(x) and 0 <= y <= BUILD_HEIGHT and (x, y) in chunk.blocks:
            return chunk.blocks[(x, y)]
    return None

def isOnGround(app, x, y):
    groundLeft = getGround(app, math.floor(x), y)
    groundRight = getGround(app, math.floor(x + 0.8), y)
    if y - groundLeft <= 0.4 or y - groundRight <= 0.4:
        return True
    return False

def getCoordsFromPix(app, xPix, yPix):
    blockY = math.ceil(-(yPix - app.height * TERRAIN_HEIGHT) / UNIT_WH) + app.player.y
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
    return (app.height * TERRAIN_HEIGHT) + ((app.player.y - y) * UNIT_WH)

def getGround(app, x, y, ignoreHalfBlocks = False):
    for chunk in app.game.loaded:
        if chunk.inChunk(x):
            for r in range(math.ceil(y), -1, -1):
                if (x, r) in chunk.blocks and chunk.blocks[(x, r)].solid:
                    if (not ignoreHalfBlocks) and chunk.blocks[(x, r)].solid == 0.5:
                        return getGround(app, x, y, True)
                    else:
                        return chunk.blocks[(x, r)].y + 1
    return -1

def generateChunks(app):
    while min(app.game.loaded).index < min(app.game.chunks.values()).index + 2:
        app.game.generateChunk(app, False)
    while max(app.game.loaded).index > max(app.game.chunks.values()).index - 2:
        app.game.generateChunk(app, True)

def moveBlock(app, block, canvas):
    x, y = getPixFromCoords(app, block.x, block.y)
    if block.type == Blocks.AIR:
        return
    image = block.image
    if image == None:
        return
    canvas.moveto(image, x, y)

def checkBackground(app):
    width = app.background.get_width()
    if min(app.game.bgX) > 0: # Left
            app.game.bgX = [min(app.game.bgX) - width] + app.game.bgX
    if max(app.game.bgX) < app.width: # Right
            app.game.bgX = app.game.bgX + [max(app.game.bgX) + width]

    newList = []
    for i in app.game.bgX: # Garbage Collector
        if i > - app.background.get_width():
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
    return app.images[name]

def withinBounds(x1, y1, x2, y2, x, y):
    return x1 <= x <= x2 and y1 <= y <= y2

# create a "height map" for a chunk with a start y and end y
# check readme for link to algo
def generateTerrain(y1, y2, displace=1, length=0):
    if 2**(length + 1) >= CHUNK_SIZE:
        return [y1, y2]
    displacement = random.randint(0, displace)
    multiply = -1 if random.randint(0, 1) else 1
    midpoint = int(((y1 + y2) / 2) + displacement * multiply)
    length += 1
    return (generateTerrain(y1, midpoint, int(displace * 0.5), length) +
        generateTerrain(midpoint, y2, int(displace * 0.5), length))
    
def belowSurface(app, y):
    if y <= GROUND_LEVEL - GRASS_LEVEL - TERRAIN_VARIATION:
        return True
    return False

def getSurface(app, x):
    for chunk in app.game.loaded:
        if chunk.inChunk(x):
            for r in range(GROUND_LEVEL - GRASS_LEVEL - TERRAIN_VARIATION,
                            GROUND_LEVEL - GRASS_LEVEL + TERRAIN_VARIATION):
                if (x, r) in chunk.blocks and chunk.blocks[(x, r)].type == Blocks.AIR:
                    if (x, r + 1) not in chunk.blocks:
                        return r
    return -1

def getBackgroundColor(time):
    lastR, lastG, lastB = colors[math.floor(time)]
    nextR, nextG, nextB = colors[math.floor(time) + 1]
    percentage = (time - math.floor(time)) * 100
    r = lastR + (nextR - lastR) * percentage / 100
    g = lastG + (nextG - lastG) * percentage / 100
    b = lastB + (nextB - lastB) * percentage / 100
    return "#%02x%02x%02x" % (int(r), int(g), int(b))

def hasOverlap(r1, r2):
    x1, y1, x2, y2 = r1
    x3, y3, x4, y4 = r2
    return (x1 <= x3 <= x2 or x1 <= x4 <= x2) and (y1 <= y3 <= y2 or y1 <= y4 <= y2)

def isOverEnemy(app, x, y):
    chunkIndex = app.game.getChunkIndex(x)
    chunk = app.game.getChunk(app, chunkIndex)
    for mob in chunk.mobs:
        width = mob.width / UNIT_WH
        height = mob.height / UNIT_WH
        margin = 0.4
        if withinBounds(mob.x - width / 2 - margin, mob.y - height / 2 - margin,
                        mob.x + width / 2 + margin, mob.y + height / 2, x, y):
            return mob
    return False

def canBeMade(app, recipe):
    items = {}
    for inv in app.player.inventory:
        if not inv: continue
        if inv.name in items.keys():
            items[inv.name] += inv.count
        else:
            items[inv.name] = inv.count
    for name, count in recipe["ingredients"].items():
        if name not in items or items[name] < count:
            return False
    return True

def makeRecipe(app, recipe):
    for item, count in recipe["ingredients"].items():
        app.player.removeItem(app, item, count)
    app.player.pickUp(app, copy.deepcopy(recipe["output"]))

def numCanCraft(app, recipe):
    if not canBeMade(app, recipe): return
    items = {}
    for inv in app.player.inventory:
        if not inv: continue
        if inv.name in items.keys():
            items[inv.name] += inv.count
        else:
            items[inv.name] = inv.count
    
    # get maximum number of recipe that can be made
    maxCount = 0
    for name, count in recipe["ingredients"].items():
        if name not in items:
            return 0
        maxCount += items[name] // count
    return maxCount

def getColors(image):
    im  = np.array(image)

    colors = []

    for x in range(im.shape[1]):
        row = []
        for y in range(im.shape[0]):
            row.append(tuple(im[y, x]))
        colors.append(row)
    
    return colors

def nearbySolid(app, x, y):
    solid = []
    block = getBlockFromCoords(app, x - 1, y)
    if block and block.solid == 1:
        solid.append(block)
    block = getBlockFromCoords(app, x + 1, y)
    if block and block.solid == 1:
        solid.append(block)
    block = getBlockFromCoords(app, x, y - 1)
    if block and block.solid == 1:
        solid.append(block)
    block = getBlockFromCoords(app, x, y + 1)
    if block and block.solid == 1:
        solid.append(block)
    
    return solid

def nearbyAir(app, x, y):
    air = []
    block = getBlockFromCoords(app, x - 1, y)
    if block and block.type == Blocks.AIR:
        air.append(block)
    block = getBlockFromCoords(app, x + 1, y)
    if block and block.type == Blocks.AIR:
        air.append(block)
    block = getBlockFromCoords(app, x, y - 1)
    if block and block.type == Blocks.AIR:
        air.append(block)
    block = getBlockFromCoords(app, x, y + 1)
    if block and block.type == Blocks.AIR:
        air.append(block)
    
    return air

def getPath(app, x1, y1, x2, y2, depth = 0, path = [], maxDepth = 5):
    if path == []:
        path = [(x1, y1)]
    if x1 == x2 and y1 == y2:
        return path
    if depth > maxDepth:
        return False
    block1 = getBlockFromCoords(app, x1, y1)
    if not block1: return False
    block2 = getBlockFromCoords(app, x2, y2)
    if not block2: return False
    for air in nearbyAir(app, x1, y1):
        if (air.x, air.y) in path: continue
        path.append((air.x, air.y))
        if getPath(app, air.x, air.y, x2, y2, depth + 1, path, maxDepth):
            return path
        path.pop()
    return False

def keyIsNumber(k):
    nums = [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]
    return k in nums