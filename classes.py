import math
import random
from PIL import Image,ImageTk
from helpers import *
from blocks import *
from items import *

class Chunk:
    def __init__(self, app, x, chunkI):
        self.blocks = {}
        self.x = x
        self.index = chunkI
        for i in range(app.CHUNK_SIZE):
            row_ground_level = app.GROUND_LEVEL
            row_grass_level = app.GRASS_LEVEL + random.randint(0, 1)
            row_dirt_level = app.DIRT_LEVEL + random.randint(0, 1)
            for r in range(row_ground_level, -1, -1):
                if r == row_ground_level:
                    block = Air(x+i, r, chunkI)
                elif r >= row_grass_level:
                    block = Grass(x+i, r, chunkI)
                elif r > row_dirt_level:
                    block = Dirt(x+i, r, chunkI)
                elif r > 0:
                    block = Stone(x+i, r, chunkI)
                else:
                    block = Bedrock(x+i, r, chunkI)
                self.blocks[(x+i, r)] = block
                    
    def getRange(self, app):
        return self.x, self.x + app.CHUNK_SIZE
    
    def inChunk(self, app, x):
        return self.x <= x and x < self.x + app.CHUNK_SIZE
    
    def generateAir(self, app, block: Block):
        if not self.inChunk(app, block.x - 1):
            leftChunk = app.game.getChunk(app, self.index - 1)
            if (block.x - 1, block.y) not in leftChunk.blocks:
                leftChunk.blocks[(block.x - 1, block.y)] = Air(block.x - 1, block.y,
                                                        self.index - 1)
        elif (block.x - 1, block.y) not in self.blocks:
            self.blocks[(block.x - 1, block.y)] = Air(block.x - 1, block.y,
                                                        self.index)
        if not self.inChunk(app, block.x + 1):
            rightChunk = app.game.getChunk(app, self.index + 1)
            if (block.x + 1, block.y) not in rightChunk.blocks:
                rightChunk.blocks[(block.x + 1, block.y)] = Air(block.x + 1, block.y,
                                                        self.index + 1)
        elif (block.x + 1, block.y) not in self.blocks:
            self.blocks[(block.x + 1, block.y)] = Air(block.x + 1, block.y,
                                                        self.index)
        if (block.x, block.y + 1) not in self.blocks:
            self.blocks[(block.x, block.y + 1)] = Air(block.x, block.y + 1,
                                                        self.index)
        if (block.x, block.y - 1) not in self.blocks:
            self.blocks[(block.x, block.y - 1)] = Air(block.x, block.y - 1,
                                                        self.index)

    def load(self, app, canvas):
        for b in self.blocks:
            block = self.blocks[b]
            if not block.image:
                block.load(app, canvas)

    def __eq__(self, other):
        return self.index == other.index
    def __gt__(self, other):
        return self.index > other.index
    def __str__(self):
        return f'I:{self.index} X:{self.x}'

class Game:
    def __init__(self, app):
        self.chunks = {}

        self.time = 0
        self.bgX = [0, app.background.width(), -app.background.width()]
        for i in range(20):
            chunkX = (i - 10) * app.CHUNK_SIZE + 2
            self.chunks[i] = Chunk(app, chunkX, i)
        
        self.loaded = []

    def generateChunk(self, app, right):
        if right:
            highest = max(self.chunks)
            chunk = Chunk(app, self.chunks[highest].x + app.CHUNK_SIZE, len(self.chunks))
            self.chunks[len(self.chunks)] = chunk
        else:
            lowest = min(self.chunks)
            chunk = Chunk(app, self.chunks[lowest].x - app.CHUNK_SIZE, lowest - 1)
            self.chunks[lowest - 1] = chunk
            
    def getChunk(self, app, i) -> Chunk:
        if i in self.chunks:
            return self.chunks[i]
        else:
            while i not in self.chunks:
                self.generateChunk(app, i > 10)
            return self.chunks[i]

    def getChunkIndex(self, x) -> int:
        for ci in self.chunks:
            chunk = self.chunks[ci]
            if chunk.x == x:
                return ci

    def loadChunks(self, app, canvas):
        chunksOnScreen = int(app.width / (app.CHUNK_SIZE * app.UNIT_WH)) + 2
        startChunkIndex = app.player.chunk - math.floor(chunksOnScreen / 2)
        endChunkIndex = startChunkIndex + chunksOnScreen
        self.loaded = [self.chunks[i] for i in self.chunks if startChunkIndex <= i <= endChunkIndex]
        for chunk in self.loaded:
            chunk.load(app, canvas)
    
    def breakBlock(self, app, block: Block):
        chunk = self.getChunk(app, block.chunkInd)
        block = chunk.blocks[(block.x, block.y)]
        item = Item(block.type.name, canPlace=True)
        chunk.blocks[(block.x, block.y)] = Air(block.x, block.y, block.chunkInd)
        chunk.generateAir(app, block)
        return item
    
    def placeBlock(self, app, item: Item, block: Block):
        chunk = self.getChunk(app, block.chunkInd)
        if (block.x, block.y) in chunk.blocks:
            module = __import__("blocks")
            class_ = getattr(module, item.name.capitalize())
            chunk.blocks[(block.x, block.y)] = class_(block.x, block.y, block.chunkInd)
        chunk.generateAir(app, chunk.blocks[(block.x, block.y)])

class Player(Entity):
    def __init__(self, app):
        self.chunk = 9
        self.x = 0.1
        self.y = app.GROUND_LEVEL
        self.dx = 0
        self.dy = 0
        self.inventory = [None] * 9
        self.inventory[0] = Item("DIRT", app.STACK_MAX, True)
        self.orient = 1
        self.health = 20
        self.image = Image.open("assets/boris.png").resize((int(app.UNIT_WH * 0.8), int(app.UNIT_WH * 0.8)))
    
    def getSprite(self):
        image = self.image.copy()
        if self.orient == -1:
            image = image.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        return ImageTk.PhotoImage(image)

    def pickUp(self, app, item: Item):
        for i in range(len(self.inventory)):
            if not self.inventory[i]:
                self.inventory[i] = item
                return
            elif self.inventory[i] == item and self.inventory[i].count < app.STACK_MAX:
                self.inventory[i].count += 1
                return

    def update(self, app):
        self.y -= self.dy
        self.gravity(app)
        self.checkForCollision(app)
        self.x += self.dx
        for _ in range(abs(int(self.dx / 0.25))):
            parallax = 1 if self.dx < 0 else -1
            app.game.bgX = [app.game.bgX[bg] + parallax for bg in range(len(app.game.bgX))]
        self.dx *= 0.6
    
    def checkForCollision(self, app):
        blockLeft = getBlockFromCoords(app, math.floor(self.x) - 1, math.ceil(self.y))
        blockRight = getBlockFromCoords(app, math.ceil(self.x), math.ceil(self.y))
        blockTop = getBlockFromCoords(app, int(self.x), int(self.y + 1))
        selfCoords = getPixFromCoords(app, self.x + self.dx, self.y)
        
        # Right Collision
        if 0 < self.dx < 1:
            if blockRight and blockRight.solid:
                self.dx = 0
                self.x = blockRight.x - 0.9

        # Left Collision
        if -1 < self.dx < 0:
            if blockLeft and blockLeft.solid:
                self.dx = 0
                self.x = blockLeft.x + 1.1
        
        # Top Collision
        if self.dy < 0 and blockTop and blockTop.solid:
            self.dy = 0
            self.y = blockTop.y - 1
        
        # Gravity Collision
        if isOnGround(app) and self.dy >= 0:
            self.dy = 0
            groundLeft = getGround(app, math.floor(app.player.x))
            groundRight = getGround(app, math.floor(app.player.x + 0.8))
            self.y = max(groundLeft, groundRight)
    
    def gravity(self, app):
        self.dy += 0.2
    
    def moveLeft(self, app, dx=-0.8):
        ground = getGround(app, math.floor(self.x)) - 1
        self.orient = -1
        self.dx = dx
        curBlock = getBlockFromCoords(app, math.floor(self.x) - 1, ground)
        if not curBlock:
            return
        newChunk = curBlock.chunkInd
        if newChunk < self.chunk:
            app.game.loaded.pop(-1)
            chunkIndex = app.game.getChunkIndex(min(app.game.loaded).x - app.CHUNK_SIZE)
            app.game.loaded.insert(0, app.game.getChunk(app, chunkIndex))
        self.chunk = newChunk
    
    def moveRight(self, app, dx=0.8):
        ground = getGround(app, math.ceil(self.x)) - 1
        self.orient = 1
        self.dx = dx
        curBlock = getBlockFromCoords(app, math.ceil(self.x) + 1, ground)
        if not curBlock:
            return
        newChunk = curBlock.chunkInd
        if newChunk > self.chunk:
            app.game.loaded.pop(0)
            chunkIndex = app.game.getChunkIndex(max(app.game.loaded).x + app.CHUNK_SIZE)
            app.game.loaded.append(app.game.getChunk(app, chunkIndex))
        self.chunk = newChunk

class Functionality:
    def __init__(self, app):
        self.mouseX = 0
        self.mouseY = 0
        self.hovering = None
        self.hoveringRect = None
        self.debug = True
        self.selectedInventory = 0
        self.keys = []
        self.keysDelay = 10
        self.keysTimer = 0
        self.canInteract = False
    
    def handleKey(self, app, key):
        """
        GAME
        """
        generateChunks(app)
        """
        PLAYER
        """
        if key.isupper():
            slow = 0.5
            key = key.lower()
        else:
            slow = 1

        if "w" == key and isOnGround(app):
            app.player.dy += -0.8 * slow
        
        if "a" == key:
            app.player.moveLeft(app, -0.8 * slow)
        elif "d" == key:
            app.player.moveRight(app, 0.8 * slow)
        checkBackground(app)
        """
        FUNC
        """
        if "/" == key:
            app.func.debug = not app.func.debug
        if key.isnumeric():
            key = int(key)
            if key != 0: app.func.selectedInventory = key - 1
    
    def handleKeys(self, app):
        for _ in range(len(self.keys)):
            self.handleKey(app, self.keys[0])
            self.keys.pop(0)
    
    def updateHovering(self, app, event):
        coords = getCoordsFromPix(app, event.x, event.y)
        if coords:
            app.func.hovering = getBlockFromCoords(app, coords[0], coords[1])

            blockPix = coords[0], coords[1]
            playerPix = int(app.player.x), int(app.player.y)
            distance = math.dist(blockPix, playerPix)

            onPlayer = int(app.func.hovering.x) == int(app.player.x) and int(app.func.hovering.y) == int(app.player.y)

            isBedrock = app.func.hovering.type == Blocks.BEDROCK
            app.func.canInteract = ((not onPlayer) and distance < 4 and (not isBedrock)) or self.debug
        else:
            app.func.hovering = None
