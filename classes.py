import math
import random
from PIL import Image,ImageTk
from helpers import *
from blocks import *
from items import *
from settings import *

class Chunk:
    def __init__(self, app, x, chunkI):
        self.blocks = {}
        self.x = x
        self.index = chunkI
        self.items = []
        for i in range(CHUNK_SIZE):
            row_ground_level = GROUND_LEVEL
            row_grass_level = GRASS_LEVEL + random.randint(0, 1)
            row_dirt_level = DIRT_LEVEL + random.randint(0, 1)
            for r in range(row_ground_level, -1, -1):
                if r == row_ground_level: # 24
                    block = Air(x+i, r, chunkI)
                elif r >= row_grass_level: # 9
                    block = Grass(x+i, r, chunkI)
                elif r > row_dirt_level: # 4
                    block = Dirt(x+i, r, chunkI)
                elif r > 0: # 0
                    block = Stone(x+i, r, chunkI)
                else: # -1
                    block = Bedrock(x+i, r, chunkI)
                self.blocks[(x+i, r)] = block
                    
    def getRange(self, app):
        return self.x, self.x + CHUNK_SIZE
    
    def inChunk(self, app, x):
        return self.x <= x and x < self.x + CHUNK_SIZE
    
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
    
    def update(self, app):
        for item in self.items:
            item.updateWrapper(app, self)
            if item.x < self.x or item.x > self.x + CHUNK_SIZE:
                self.items.remove(item)
                if item.x < self.x:
                    newChunk = app.game.getChunk(app, self.index - 1)
                else:
                    newChunk = app.game.getChunk(app, self.index + 1)
                newChunk.items.append(item)

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
            chunkX = (i - 10) * CHUNK_SIZE + 2
            self.chunks[i] = Chunk(app, chunkX, i)
        
        self.chunks[9].items.append(Item("carrot", self.chunks[9].x + 1, GROUND_LEVEL, 9))
        
        self.loaded = []

    def generateChunk(self, app, right):
        if right:
            highest = max(self.chunks)
            chunk = Chunk(app, self.chunks[highest].x + CHUNK_SIZE, len(self.chunks))
            self.chunks[len(self.chunks)] = chunk
        else:
            lowest = min(self.chunks)
            chunk = Chunk(app, self.chunks[lowest].x - CHUNK_SIZE, lowest - 1)
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
        chunksOnScreen = int(app.width / (CHUNK_SIZE * UNIT_WH)) + 2
        startChunkIndex = app.player.chunk - math.floor(chunksOnScreen / 2)
        endChunkIndex = startChunkIndex + chunksOnScreen
        self.loaded = [self.chunks[i] for i in self.chunks if startChunkIndex <= i <= endChunkIndex]
        for chunk in self.loaded:
            chunk.load(app, canvas)
    
    def breakBlock(self, app, block: Block):
        chunk = self.getChunk(app, block.chunkInd)
        block = chunk.blocks[(block.x, block.y)]
        item = InventoryItem(block.type.name, canPlace=True)
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
    def __init__(self):
        self.chunk = 9

        super().__init__(0.1, GROUND_LEVEL)
        self.inventory = [InventoryItem("DIRT", STACK_MAX, True)] + [None] * 8
        self.orient = 1
        self.health = 20
        self.image = Image.open("assets/boris.png").resize((int(UNIT_WH * 0.8), int(UNIT_WH * 0.8)))
    
    def getSprite(self):
        image = self.image.copy()
        if self.orient == -1:
            image = image.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        return ImageTk.PhotoImage(image)

    def pickUp(self, app, item: InventoryItem):
        for i in range(len(self.inventory)):
            if not self.inventory[i]:
                self.inventory[i] = item
                return
            elif self.inventory[i] == item and self.inventory[i].count < STACK_MAX:
                self.inventory[i].count += item.count
                return
        self.throwItem(app, item)
    
    def throwItem(self, app, item: InventoryItem, inInventory=False):
        newX = self.x - 1
        dx = -0.4
        if self.orient == 1:
            newX = self.x + 1
            dx = 0.4
        chunk = app.game.getChunk(app, self.chunk)
        chunk.items.append(
            item.toItem(self.chunk, newX, self.y, canPickUp=False, dx=dx, dy=-0.3)
        )
        if inInventory:
            self.inventory[app.func.selectedInventory] = None

    def update(self, app):
        for _ in range(abs(int(self.dx / 0.25))):
            parallax = 1 if self.dx < 0 else -1
            app.game.bgX = [app.game.bgX[bg] + parallax for bg in range(len(app.game.bgX))]

    def moveLeft(self, app, dx=-0.8):
        ground = getGround(app, math.floor(self.x), self.y) - 1
        self.orient = -1
        self.dx = dx
        curBlock = getBlockFromCoords(app, math.floor(self.x) - 1, ground)
        if not curBlock:
            return
        newChunk = curBlock.chunkInd
        if newChunk < self.chunk:
            app.game.loaded.pop(-1)
            chunkIndex = app.game.getChunkIndex(min(app.game.loaded).x - CHUNK_SIZE)
            app.game.loaded.insert(0, app.game.getChunk(app, chunkIndex))
        self.chunk = newChunk
        app.func.updateHovering(app)
    
    def moveRight(self, app, dx=0.8):
        ground = getGround(app, math.ceil(self.x), self.y) - 1
        self.orient = 1
        self.dx = dx
        curBlock = getBlockFromCoords(app, math.ceil(self.x) + 1, ground)
        if not curBlock:
            return
        newChunk = curBlock.chunkInd
        if newChunk > self.chunk:
            app.game.loaded.pop(0)
            chunkIndex = app.game.getChunkIndex(max(app.game.loaded).x + CHUNK_SIZE)
            app.game.loaded.append(app.game.getChunk(app, chunkIndex))
        self.chunk = newChunk
        app.func.updateHovering(app)

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
        self.holding = None
        self.goodGraphics = False
    
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

        if "w" == key and isOnGround(app, app.player.x, app.player.y):
            app.player.dy -= 0.8 * slow
        
        if "a" == key:
            app.player.moveLeft(app, -0.8 * slow)
        elif "d" == key:
            app.player.moveRight(app, 0.8 * slow)
        checkBackground(app)

        if "q" == key:
            app.player.throwItem(app, app.player.inventory[self.selectedInventory],
                                 inInventory=True)
        """
        FUNC
        """
        if "/" == key:
            self.debug = not self.debug
        if key.isnumeric():
            key = int(key)
            if key != 0: self.selectedInventory = key - 1
        if "g" == key:
            self.goodGraphics = not self.goodGraphics
    def handleKeys(self, app):
        for _ in range(len(self.keys)):
            self.handleKey(app, self.keys[0])
            self.keys.pop(0)
    
    def updateHovering(self, app):
        coords = getCoordsFromPix(app, self.mouseX, self.mouseY)
        if coords:
            self.hovering = getBlockFromCoords(app, coords[0], coords[1])

            blockPix = coords[0], coords[1]
            playerPix = int(app.player.x), int(app.player.y)
            distance = math.dist(blockPix, playerPix)

            onPlayer = int(self.hovering.x) == int(app.player.x) and int(self.hovering.y) == int(app.player.y)

            isBedrock = app.func.hovering.type == Blocks.BEDROCK
            self.canInteract = ((not onPlayer) and distance < 4 and (not isBedrock)) or self.debug
        else:
            self.hovering = None
    
    def handleClick(self, app):
        if self.hovering and self.canInteract:
            curInv = app.player.inventory[self.selectedInventory]
            if self.hovering.breakable:
                block = app.game.breakBlock(app, self.hovering)
                app.player.pickUp(app, block)
            elif curInv and curInv.canPlace and self.hovering.type == Blocks.AIR:
                app.game.placeBlock(app, curInv, self.hovering)
                curInv.count -= 1
                if curInv.count == 0:
                    curInv = None
                app.player.inventory[self.selectedInventory] = curInv
        self.updateHovering(app)
