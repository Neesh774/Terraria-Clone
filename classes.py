import math
import random
from PIL import Image,ImageTk
from helpers import *
from blocks import *
from items import *
from settings import *

class Chunk:
    def __init__(self, app, x, chunkI,
                 startY = None, endY = None, closePoints = []):
        self.blocks = {}
        self.x = x
        self.index = chunkI
        self.items = []
        self.points = []
        self.mobs = []
        if startY:
            self.endY = GROUND_LEVEL + random.randint(-TERRAIN_VARIATION, TERRAIN_VARIATION)
            self.startY = startY
        elif endY:
            self.startY = GROUND_LEVEL + random.randint(-TERRAIN_VARIATION, TERRAIN_VARIATION)
            self.endY = endY

        # returns a height for every point in the chunk
        terrain = generateTerrain(self.startY, self.endY)
        for i in range(CHUNK_SIZE):
            height = terrain[i]
            row_ground_level = height
            row_grass_level = height - GRASS_LEVEL - random.randint(0, 2)
            row_dirt_level = height - DIRT_LEVEL - random.randint(-1, 1)
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
        
        # Create random points to make caves at
        for i in range(random.randint(0, 7)):
            point = (random.randint(self.x, self.x + CHUNK_SIZE),
                        random.randint(0, GROUND_LEVEL - GRASS_LEVEL - 5))
            radius = random.randint(2, 4)
            self.points.append({
                "coords": point,
                "radius": radius
            })
        
        # take into account self points and nearby points
        for pointObj in closePoints + self.points:
            point = pointObj["coords"]
            rad = pointObj["radius"]
            for i in range(point[0] - rad, point[0] + rad):
                for j in range(point[1] - rad, point[1] + rad):
                    dist = math.sqrt((i - point[0])**2 + (j - point[1])**2)
                    randomChance = random.randint(-1, 2)
                    if ((i, j) in self.blocks and dist <= (rad + randomChance)
                        and self.blocks[(i, j)].breakable):
                        self.blocks[(i, j)] = Air(i, j, chunkI)
                    
    def getRange(self, app):
        return self.x, self.x + CHUNK_SIZE
    
    def inChunk(self, x):
        return self.x <= x and x < self.x + CHUNK_SIZE

    def generateAir(self, app, block: Block):
        if not self.inChunk(block.x - 1):
            leftChunk = app.game.getChunk(app, self.index - 1)
            if (block.x - 1, block.y) not in leftChunk.blocks:
                leftChunk.blocks[(block.x - 1, block.y)] = Air(block.x - 1, block.y,
                                                        self.index - 1)
        elif (block.x - 1, block.y) not in self.blocks:
            self.blocks[(block.x - 1, block.y)] = Air(block.x - 1, block.y,
                                                        self.index)
        if not self.inChunk(block.x + 1):
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
        
        for mob in self.mobs:
            mob.updateWrapper(app)
            if mob.x < self.x or mob.x > self.x + CHUNK_SIZE:
                self.mobs.remove(mob)
                if mob.x < self.x:
                    newChunk = app.game.getChunk(app, self.index - 1)
                else:
                    newChunk = app.game.getChunk(app, self.index + 1)
                newChunk.mobs.append(mob)

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
        startY = GROUND_LEVEL
        for i in range(20):
            chunkX = (i - 10) * CHUNK_SIZE + 2
            if i - 1 in self.chunks:
                closePoints = self.chunks[i - 1].points
            else:
                closePoints = []
            self.chunks[i] = Chunk(app, chunkX, i, startY=startY, closePoints=closePoints)
            startY = self.chunks[i].endY
        
        self.chunks[9].mobs.append(Mushroom(app, 5, GROUND_LEVEL + 1))

        self.loaded = []

    def generateChunk(self, app, right):
        if right:
            highest = max(self.chunks)
            highest_chunk = self.chunks[highest]
            chunk = Chunk(app, self.chunks[highest].x + CHUNK_SIZE, len(self.chunks),
                          startY = highest_chunk.endY, closePoints=highest_chunk.points)
            self.chunks[len(self.chunks)] = chunk
        else:
            lowest = min(self.chunks)
            lowest_chunk = self.chunks[lowest]
            chunk = Chunk(app, self.chunks[lowest].x - CHUNK_SIZE, lowest - 1,
                          endY = lowest_chunk.startY, closePoints=lowest_chunk.points)
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
            if chunk.inChunk(x):
                return ci

    def loadChunks(self, app, canvas):
        chunksOnScreen = int(app.width / (CHUNK_SIZE * UNIT_WH)) + 2
        startChunkIndex = app.player.chunk - math.floor(chunksOnScreen / 2)
        endChunkIndex = startChunkIndex + chunksOnScreen
        self.loaded = [self.chunks[i] for i in self.chunks if startChunkIndex <= i <= endChunkIndex]
        for chunk in self.loaded:
            chunk.load(app, canvas)
    
    def breakBlock(self, app, block: Block, drop=True):
        chunk = self.getChunk(app, block.chunkInd)
        block = chunk.blocks[(block.x, block.y)]
        item = Item(block.type.name, block.x, block.y, block.chunkInd, canPlace=True)
        chunk.blocks[(block.x, block.y)] = Air(block.x, block.y, block.chunkInd)
        chunk.generateAir(app, block)
        chunk.items.append(item)
        return item

    def placeBlock(self, app, item: Item, block: Block):
        if block.y >= BUILD_HEIGHT or block.y <= 0:
            return False
        chunk = self.getChunk(app, block.chunkInd)
        if (block.x, block.y) in chunk.blocks:
            module = __import__("blocks")
            class_ = getattr(module, item.name.capitalize())
            chunk.blocks[(block.x, block.y)] = class_(block.x, block.y, block.chunkInd)
            chunk.generateAir(app, chunk.blocks[(block.x, block.y)])
            return True

class Player(Entity):
    def __init__(self):
        super().__init__(0.1, GROUND_LEVEL)
        self.chunk = 9
        self.inventory = [InventoryItem("DIRT", STACK_MAX, True)] + [None] * 8
        self.orient = 1
        self.health = 10
        self.falling = 0
        self.respawnPoint = (0.1, GROUND_LEVEL)
        self.sneak = False
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
        if item:
            newX = self.x - 1
            dx = -0.4
            if self.orient == 1:
                newX = self.x + 1
                dx = 0.4
            chunk = app.game.getChunk(app, self.chunk)
            chunk.items.append(
                item.toItem(self.chunk, newX, self.y, count=1,  canPickUp=False, dx=dx, dy=-0.3)
            )
            if inInventory:
                item.count -= 1
                if item.count == 0:
                    self.inventory[app.func.selectedInventory] = None
                else:
                    self.inventory[app.func.selectedInventory] = item

    def update(self, app):
        if FALL_DAMAGE:
            if self.dy > 0:
                self.falling += 1
            else:
                if self.falling > 12:
                    dist = self.falling - 12
                    self.health -= dist
                self.falling = 0
        if self.health <= 0:
            app.paused = True
            app.deathScreen = True
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
    
    def die(self, app):
        # drop items
        chunk = app.game.getChunk(app, self.chunk)
        for item in self.inventory:
            if not item: continue
            chunk.items.append(item.toItem(self.chunk, self.x, self.y, canPickUp=True, count=item.count))
        
        # check around respawn point for valid spawn point
        block = getBlockFromCoords(app, self.respawnPoint[0], self.respawnPoint[1])
        while block and block.solid:
            self.respawnPoint = (self.respawnPoint[0] + 1, self.respawnPoint[1])
            block = getBlockFromCoords(app, self.respawnPoint[0], self.respawnPoint[1])
        self.x, self.y = self.respawnPoint
        self.health = 10
        self.falling = 0
        self.dx = 0
        self.dy = 0
        self.orient = 1
        self.chunk = 9
        
        self.inventory = [None] * 9
    
    def hit(self, app, isRight):
        curChunk = app.game.getChunk(app, self.chunk)
        rightChunk = app.game.getChunk(app, self.chunk + 1)
        mobs = curChunk.mobs + rightChunk.mobs
        for mob in mobs:
            if isRight:
                withinXRange = mob.x > self.x and mob.x < self.x + 2
                withinYRange = mob.y >= self.y and mob.y <= self.y + 1
                if withinXRange and withinYRange:
                    mob.takeDamage(app, 1)
            else:
                withinXRange = mob.x < self.x and mob.x > self.x - 2
                withinYRange = mob.y >= self.y and mob.y <= self.y + 1
                if withinXRange and withinYRange:
                    mob.takeDamage(app, 1)
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
        self.keybinds = False
    
    def handleKey(self, app, key):
        """
        FUNC
        """
        if "k" == key or (self.keybinds and "Escape" == key):
            self.keybinds = not self.keybinds
        if self.keybinds:
            return
        if "/" == key:
            self.debug = not self.debug
        if key.isnumeric():
            num = int(key)
            if num != 0: self.selectedInventory = num - 1
        if "g" == key:
            self.goodGraphics = not self.goodGraphics

        """
        PLAYER
        """
        if key.isupper():
            app.player.sneak = True
            slow = 0.5
            key = key.lower()
        else:
            app.player.sneak = False
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
        GAME
        """
        generateChunks(app)

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
            x = app.player.x
            y = app.player.y
            onPlayer = (withinBounds(coords[0], coords[1], coords[0] + 1, coords[1] + 1, x, y + 0.4)
                or withinBounds(coords[0], coords[1], coords[0] + 1, coords[1] + 1, x + 0.8, y + 0.4))

            isBedrock = app.func.hovering.type == Blocks.BEDROCK
            self.canInteract = ((not onPlayer) and distance < 4 and (not isBedrock)) or self.debug
        else:
            self.hovering = None
    
    def handleClick(self, app):
        if self.hovering and self.canInteract:
            curInv = app.player.inventory[self.selectedInventory]
            if self.hovering.breakable:
                app.game.breakBlock(app, self.hovering)
            elif curInv and curInv.canPlace and self.hovering.type == Blocks.AIR:
                if app.game.placeBlock(app, curInv, self.hovering):
                    curInv.count -= 1
                    if curInv.count == 0:
                        curInv = None
                    app.player.inventory[self.selectedInventory] = curInv
        self.updateHovering(app)

class Mushroom(Entity):
    def __init__(self, app, x, y):
        super().__init__(x, y)
        self.health = 5
        self.viewRange = 10
        self.attackRange = 1
        self.orient = 1
        self.damage = 0.5
        self.damageCooldown = 0
        self.idle = []
        self.width = 32
        self.height = 32
        idleSprites = app.images["mush-idle"]
        for i in range(14):
            sprite = idleSprites.crop((32 * i, 0, 32 * (i + 1), 32))
            self.idle.append(sprite)
        self.run = []
        runSprites = app.images["mush-run"]
        for i in range(16):
            sprite = runSprites.crop((32 * i, 0, 32 * (i + 1), 32))
            self.run.append(sprite)
        self.spriteIndex = 0
        self.isHurt = -1
        self.hurt = []
        hurtSprites = app.images["mush-hit"]
        for i in range(5):
            sprite = hurtSprites.crop((32 * i, 0, 32 * (i + 1), 32))
            self.hurt.append(sprite)
    def update(self, app):
        # check if player is in range
        dist = math.dist((self.x, self.y), (app.player.x, app.player.y))
        if dist < self.attackRange and self.damageCooldown == 0:
            self.attack(app)
        elif dist < self.viewRange and dist > 1:
            if self.x < app.player.x:
                self.moveRight()
            elif self.x > app.player.x:
                self.moveLeft()
        
        if self.damageCooldown > 0:
            self.damageCooldown -= 0.2
        if self.damageCooldown < 0:
            self.damageCooldown = 0
        
        if self.isHurt >= 0:
            self.isHurt += 1
            if self.isHurt == 4:
                self.isHurt = -1
            self.spriteIndex = self.isHurt
        elif self.dx != 0 or self.dy != 0:
            self.spriteIndex = (self.spriteIndex + 1) % len(self.run)
        else:
            self.spriteIndex = (self.spriteIndex + 1) % len(self.idle)
    
    def draw(self, app, canvas):
        x = getPixX(app, self.x)
        y = getPixY(app, self.y)
        if self.isHurt >= 0:
            sprite = self.hurt[self.spriteIndex]
        elif self.dx != 0 or self.dy != 0:
            sprite = self.run[self.spriteIndex]
        else:
            sprite = self.idle[self.spriteIndex]
        canvas.create_image(x, y, image=ImageTk.PhotoImage(sprite))
        
    def moveRight(self):
        self.dx += 0.05
        self.orient = 1
    def moveLeft(self):
        self.dx -= 0.05
        self.orient = -1
    
    def attack(self, app):
        app.player.health -= self.damage
        if self.x < app.player.x:
            app.player.dy -= 0.2
            app.player.dx += 0.2
        else:
            app.player.dy -= 0.2
            app.player.dx -= 0.2
        if app.player.health <= 0:
            app.paused = True
            app.deathScreen = True
        self.damageCooldown = 5
    
    def takeDamage(self, app, damage):
        self.health -= damage
        if self.health <= 0:
            self.die(app)
        if app.player.x < self.x:
            self.dx += 0.6
        else:
            self.dx -= 0.6
        self.dy -= 0.2
        self.isHurt = 0
        self.spriteIndex = 0
    
    def die(self, app):
        chunk = app.game.getChunk(app, app.game.getChunkIndex(self.x))
        chunk.mobs.remove(self)
        drop = Item("carrot", self.x, self.y, chunk, random.randint(1, 3), dy=-0.5)
        chunk.items.append(drop)
