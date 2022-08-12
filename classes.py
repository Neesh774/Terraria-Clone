from curses import KEY_ENTER
import math
import random
from helpers import *
from blocks import *
from items import *
from settings import *
from recipes import *
from mobs import *

import pygame
from pygame.locals import *
from pygame.key import *

class Chunk:
    def __init__(self, app, x, chunkI,
                 startY = None, endY = None, closePoints = []):
        self.blocks = {}
        self.x = x
        self.index = chunkI
        self.items = pygame.sprite.Group()
        self.points = []
        self.mobs = pygame.sprite.Group()
        if startY:
            self.endY = GROUND_LEVEL + random.randint(-TERRAIN_VARIATION, TERRAIN_VARIATION)
            self.startY = startY
        elif endY:
            self.startY = GROUND_LEVEL + random.randint(-TERRAIN_VARIATION, TERRAIN_VARIATION)
            self.endY = endY

        # returns a height for every point in the chunk
        terrain = generateTerrain(self.startY, self.endY)
        self.terrain = terrain
        chunkTrees = 0
        for i in range(CHUNK_SIZE):
            height = terrain[i]
            row_ground_level = height
            row_grass_level = height - GRASS_LEVEL - random.randint(0, 2)
            row_dirt_level = height - DIRT_LEVEL - random.randint(-1, 1)
            for r in range(row_ground_level, -1, -1):
                if r >= row_ground_level: # 24
                    block = Air(app, x+i, r, chunkI, darkness = height - r - 2)
                elif r >= row_grass_level: # 9
                    block = Grass(app, x+i, r, chunkI, darkness = height - r - 2)
                elif r > row_dirt_level: # 4
                    block = Dirt(app, x+i, r, chunkI, darkness = height - r - 2)
                elif r > 0: # 0
                    block = Stone(app, x+i, r, chunkI, darkness = height - r - 2)
                else: # -1
                    block = Bedrock(app, x+i, r, chunkI, darkness = height - r - 2)
                self.blocks[(x+i, r)] = block
                
            if random.randint(0, 15) == 0 and chunkTrees < 3:
                chunkTrees += 1
                treeHeight = random.randint(8, 14)
                for j in range(0, treeHeight):
                    self.blocks[(x + i, row_ground_level + j)] = Tree(app, x + i, row_ground_level + j, chunkI)
        
        self.generatePoints(app)
        
        # take into account self points and nearby points
        for pointObj in closePoints + self.points:
            point = pointObj["coords"]
            rad = pointObj["radius"]
            pointType = pointObj["type"]
            for i in range(point[0] - rad, point[0] + rad):
                for j in range(point[1] - rad, point[1] + rad):
                    dist = math.sqrt((i - point[0])**2 + (j - point[1])**2)
                    randomChance = random.randint(-1, 2)
                    if ((i, j) in self.blocks and dist <= (rad + randomChance)
                        and self.blocks[(i, j)].breakable):
                        self.blocks[(i, j)].kill()
                        if pointType == TerrainPoints.CAVE:
                            self.blocks[(i, j)] = Air(app, i, j, chunkI, darkness = 4)
                        elif pointType == TerrainPoints.ANDESITE:
                            self.blocks[(i, j)] = Andesite(app, i, j, chunkI, darkness = 4)
                        elif pointType == TerrainPoints.DIORITE:
                            self.blocks[(i, j)] = Diorite(app, i, j, chunkI, darkness = 4)
                        elif pointType == TerrainPoints.IRON:
                            self.blocks[(i, j)] = IronOre(app, i, j, chunkI, darkness = 4)
                        elif pointType == TerrainPoints.BIRD_SPAWN:
                            self.blocks[(i, j)] = BirdSpawn(app, i, j, chunkI, darkness = 4)
    
    def getRange(self, app):
        return self.x, self.x + CHUNK_SIZE
    
    def inChunk(self, x):
        return self.x <= x and x < self.x + CHUNK_SIZE

    def generateAir(self, app, block: Block):
        for x in range(block.x - 1, block.x + 2):
            for y in range(block.y - 1, block.y + 2):
                if not self.inChunk(x):
                    if x <= self.x:
                        leftChunk = app.game.getChunk(app, self.index - 1)
                        if (x, y) not in leftChunk.blocks:
                            leftChunk.blocks[(x, y)] = Air(app, x, y, self.index - 1)
                    elif x >= self.x + CHUNK_SIZE:
                        rightChunk = app.game.getChunk(app, self.index + 1)
                        if (x, y) not in rightChunk.blocks:
                            rightChunk.blocks[(x, y)] = Air(app, x, y, self.index + 1)
                elif ((x, y) not in self.blocks):
                    self.blocks[(x, y)] = Air(app, x, y, self.index)
    
    def ungenerateAir(self, app, block: Block):
        for x in range(block.x - 1, block.x + 2):
            for y in range(block.y - 1, block.y + 2):
                nearbySolids = nearbySolid(app, x, y)
                if not self.inChunk(x):
                    if x <= self.x:
                        leftChunk = app.game.getChunk(app, self.index - 1)
                        if (x, y) in leftChunk.blocks and leftChunk.blocks[(x, y)].type == Blocks.AIR:
                            if len(nearbySolids) == 0:
                                app.game.blocks.remove(leftChunk.blocks[(x, y)])
                                del leftChunk.blocks[(x, y)]
                    elif x >= self.x + CHUNK_SIZE:
                        rightChunk = app.game.getChunk(app, self.index + 1)
                        if (x, y) in rightChunk.blocks and rightChunk.blocks[(x, y)].type == Blocks.AIR:
                            if len(nearbySolids) == 0:
                                app.game.blocks.remove(rightChunk.blocks[(x, y)])
                                del rightChunk.blocks[(x, y)]
                elif ((x, y) in self.blocks and self.blocks[(x, y)].type == Blocks.AIR):
                    if len(nearbySolids) == 0:
                        app.game.blocks.remove(self.blocks[(x, y)])
                        del self.blocks[(x, y)]
    
    def update(self, app):
        for item in self.items:
            item.update(app, self)
            if item.x < self.x or item.x > self.x + CHUNK_SIZE:
                try:
                    self.items.remove(item)
                    if item.x < self.x:
                        newChunk = app.game.getChunk(app, self.index - 1)
                    else:
                        newChunk = app.game.getChunk(app, self.index + 1)
                    newChunk.items.add(item)
                except Exception:
                    pass
        
        for mob in self.mobs:
            mob.update(app)
            if mob.x < self.x or mob.x > self.x + CHUNK_SIZE:
                self.mobs.remove(mob)
                if mob.x < self.x:
                    newChunk = app.game.getChunk(app, self.index - 1)
                else:
                    newChunk = app.game.getChunk(app, self.index + 1)
                newChunk.mobs.add(mob)
    
    def generatePoints(self, app):
        # Generate terrain points to be used for caves or stone generation
        for i in range(random.randint(0, 10)):
            typeRand = random.randint(0, 5)
            if typeRand < 2:
                pointType = TerrainPoints.CAVE
                radius = random.randint(2, 6)
                y = random.randint(0, GROUND_LEVEL - GRASS_LEVEL - 5)
            elif typeRand == 2:
                pointType = TerrainPoints.ANDESITE
                radius = random.randint(3, 4)
                y = random.randint(0, GROUND_LEVEL - DIRT_LEVEL - 6)
            elif typeRand == 3:
                pointType = TerrainPoints.DIORITE
                radius = random.randint(1, 3)
                y = random.randint(0, GROUND_LEVEL - DIRT_LEVEL - 10)
            elif typeRand == 4:
                pointType = TerrainPoints.IRON
                radius = random.randint(1, 2)
                y = random.randint(0, GROUND_LEVEL - GRASS_LEVEL - 10)
            elif typeRand == 5:
                willSpawnBirdSpawn = random.randint(0, 10)
                if willSpawnBirdSpawn == 10:
                    pointType = TerrainPoints.BIRD_SPAWN
                    radius = 1
                    y = random.randint(0, 10)
                else:
                    continue
            point = (random.randint(self.x, self.x + CHUNK_SIZE), y)
            self.points.append({
                "coords": point,
                "radius": radius,
                "type": pointType
            })

    def __eq__(self, other):
        return self.index == other.index
    def __gt__(self, other):
        return self.index > other.index
    def __str__(self):
        return f'I:{self.index} X:{self.x}'

class Game:
    def __init__(self, app):
        app.game = self
        self.chunks = {}
        self.blocks = pygame.sprite.Group()
        self.time = 0
        self.bgX = [0, app.background.get_width(), -app.background.get_width()]
        startY = GROUND_LEVEL
        for i in range(20):
            chunkX = (i - 10) * CHUNK_SIZE + 2
            if i - 1 in self.chunks:
                closePoints = self.chunks[i - 1].points
            else:
                closePoints = []
            self.chunks[i] = Chunk(app, chunkX, i, startY=startY, closePoints=closePoints)
            startY = self.chunks[i].endY
        
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

    def loadChunks(self, app):
        chunksOnScreen = int(app.width / (CHUNK_SIZE * UNIT_WH)) + 2
        startChunkIndex = app.player.chunk - math.floor(chunksOnScreen / 2)
        endChunkIndex = startChunkIndex + chunksOnScreen
        loaded = [self.chunks[i] for i in self.chunks if startChunkIndex <= i <= endChunkIndex]

        for chunk in self.loaded:
            self.blocks.remove(*chunk.blocks.values())
        
        for chunk in loaded:
            self.blocks.add(*chunk.blocks.values())

        self.loaded = loaded

    def placeBlock(self, app, item: Item, block: Block):
        if block.y >= BUILD_HEIGHT or block.y <= 0:
            return False
        chunk = self.getChunk(app, block.chunkInd)
        if (block.x, block.y) in chunk.blocks:
            module = __import__("blocks")
            class_ = getattr(module, item.name.capitalize())
            chunk.blocks[(block.x, block.y)] = class_(app, block.x, block.y, block.chunkInd)
            chunk.generateAir(app, chunk.blocks[(block.x, block.y)])
            item.count -= 1
            if item.count == 0:
                item = None
            app.player.inventory[app.func.selectedInventory] = item
            return True
    
    def spawnRandomMob(self, app):
        # loop through blocks within PLAYER_MOB_SPAWN_RADIUS of player
        left_side = int(app.player.x - PLAYER_MOB_SPAWN_RADIUS)
        right_side = int(app.player.x + PLAYER_MOB_SPAWN_RADIUS)
        top_side = int(app.player.y - PLAYER_MOB_SPAWN_RADIUS)
        bottom_side = int(app.player.y + PLAYER_MOB_SPAWN_RADIUS)
        x = random.randint(left_side, right_side)
        y = random.randint(top_side, bottom_side)
        if x > app.player.x - 3 and x < app.player.x + 3: # within player
            return
        if y > app.player.y - 3 and y < app.player.y + 3:
            return
        block = getBlockFromCoords(app, x, y)
        if not block or block.solid: # if there's no block or it's a solid block
            return
        chunk = self.getChunk(app, block.chunkInd)
        if len(chunk.mobs) >= MOB_LIMIT: # over mob limit in chunk
            return
        onGround = isOnGround(app, x, y)
        if not onGround:
            return
        for mob in chunk.mobs: # within other mob
            if mob.x - 1 < x < mob.x + 1 and mob.y - 1 < y < mob.y + 1:
                return
        if y > GROUND_LEVEL:
            mob = Mushroom(app, x, y)
        else:
            mob = Slime(app, x, y)
        if pygame.sprite.spritecollideany(mob, app.game.blocks):
            return
        self.getChunk(app, block.chunkInd).mobs.add(mob)
        return mob

    def spawnMob(self, app, mobName):
        if mobName == "slime":
            mob = Slime(app, app.player.x, app.player.y)
        elif mobName == "mushroom":
            mob = Mushroom(app, app.player.x, app.player.y)
        elif mobName == "fat_bird":
            mob = FatBird(app, app.player.x, app.player.y)
        chunk = self.getChunk(app, app.player.chunk)
        chunk.mobs.add(mob)

class Player(Entity):
    def __init__(self, app):
        self.chunk = 9
        self.inventory = [GodItem(1)] + [None] * 8
        self.orient = 1
        self.health = 10
        self.falling = 0
        self.respawnPoint = (0.1, GROUND_LEVEL)
        self.canCraft = []
        self.mineLevel = 0
        self.mineSpeed = 1


        block = getBlockFromCoords(app, self.respawnPoint[0], self.respawnPoint[1])
        tries = 0
        while (block and block.solid) or (not block):
            rand = random.randint(-2, 2)
            x = math.floor(self.respawnPoint[0] + rand)
            y = math.floor(self.respawnPoint[1] + rand)
            block = getBlockFromCoords(app, x, y)
            if block and not block.solid:
                self.respawnPoint = (x, y)
                break
            tries += 1
            if tries > 16:
                break


        super().__init__(self.respawnPoint[0], self.respawnPoint[1])
        self.sneak = False
        self.originalImage = pygame.transform.scale(getImage(app, "boris"), (int(UNIT_WH * 0.8), int(UNIT_WH * 0.8)))
        self.image = self.originalImage
        self.rect = self.image.get_rect()

        self.suffocationDamage = True
        self.spawnInvincibility = 0

    def getSprite(self):
        if self.orient == -1:
            return pygame.transform.flip(self.image, True, False)
        return self.image

    def pickUp(self, app, item: InventoryItem):
        for i in range(len(self.inventory)):
            if self.inventory[i] and self.inventory[i] == item and self.inventory[i].count < STACK_MAX:
                self.inventory[i].addToCount(item.count)
                self.updateCanCraft(app)
                return
        for i in range(len(self.inventory)):
            if not self.inventory[i]:
                self.inventory[i] = item
                self.updateCanCraft(app)
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
            chunk.items.add(
                item.toItem(app, self.chunk, newX, self.y, count=1,  canPickUp=False, dx=dx, dy=-0.3)
            )
            if inInventory:
                item.count -= 1
                if item.count == 0:
                    self.inventory[app.func.selectedInventory] = None
                else:
                    self.inventory[app.func.selectedInventory] = item
        self.updateCanCraft(app)
    
    def removeItem(self, app, item, count = 1):
        for i in range(len(self.inventory)):
            if self.inventory[i] and self.inventory[i].name == item:
                self.inventory[i].count -= count
                if self.inventory[i].count == 0:
                    self.inventory[i] = None
                self.updateCanCraft(app)
                return

    def tick(self, app):
        if FALL_DAMAGE and self.spawnInvincibility == 0:
            if self.dy > 0:
                self.falling += 1
            else:
                if self.falling > 24:
                    dist = self.falling - 24
                    self.health -= dist
                self.falling = 0
        if self.spawnInvincibility > 0:
            self.spawnInvincibility -= 1
        if self.health <= 0:
            app.paused = True
            app.deathScreen = True
        for _ in range(abs(int(self.dx / 0.25))):
            parallax = 1 if self.dx < 0 else -1
            app.game.bgX = [app.game.bgX[bg] + parallax for bg in range(len(app.game.bgX))]
        
        for item in self.inventory:
            if item and hasattr(item, "curCooldown"):
                item.curCooldown -= 1
                if item.curCooldown <= 0:
                    item.curCooldown = 0
        
        if self.orient == -1:
            self.image = pygame.transform.flip(self.originalImage, True, False)
        else:
            self.image = self.originalImage

    def moveLeft(self, app, dx=-PLAYER_SPEED):
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
    
    def moveRight(self, app, dx=PLAYER_SPEED):
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
    
    def moveDown(self, app):
        curBlock = getBlockFromCoords(app, roundHalfUp(self.x), self.y - 1)
        if curBlock and curBlock.solid == 0.5:
            curBlock.toggleDensity()
    
    def die(self, app):
        # drop items
        chunk = app.game.getChunk(app, self.chunk)
        for item in self.inventory:
            if not item: continue
            chunk.items.add(item.toItem(app, self.chunk, self.x, self.y, canPickUp=True, count=item.count))
        
        # check around respawn point for valid spawn point
        block = getBlockFromCoords(app, self.respawnPoint[0], self.respawnPoint[1])
        tries = 0
        while (block and block.solid) or (not block):
            rand = random.randint(-2, 2)
            x = math.floor(self.respawnPoint[0] + rand)
            y = math.floor(self.respawnPoint[1] + rand)
            block = getBlockFromCoords(app, x, y)
            if block and not block.solid:
                self.respawnPoint = (x, y)
                break
            tries += 1
            if tries > 16:
                break
        self.x, self.y = self.respawnPoint
        self.health = 10
        self.falling = 0
        self.dx = 0
        self.dy = 0
        self.orient = 1
        self.chunk = 9
        self.spawnInvincibility = 100
        
        self.inventory = [None] * 9
    
    def hit(self, app, isRight):
        curChunk = app.game.getChunk(app, self.chunk)
        rightChunk = app.game.getChunk(app, self.chunk + 1)
        mobs = curChunk.mobs.sprites() + rightChunk.mobs.sprites()
        damage = self.getAttackDamage(app)
        curInv = self.inventory[app.func.selectedInventory]
        if curInv and hasattr(curInv, "curCooldown"):
            tool = curInv
        else:
            tool = None
        for mob in mobs:
            if isRight:
                withinXRange = mob.x > self.x and mob.x < self.x + 2
                withinYRange = mob.y >= self.y and mob.y <= self.y + 1
                if withinXRange and withinYRange:
                    mob.takeDamage(app, damage)
                    if tool:
                        tool.curCooldown = tool.attackCooldown
            else:
                withinXRange = mob.x < self.x and mob.x > self.x - 2
                withinYRange = mob.y >= self.y and mob.y <= self.y + 1
                if withinXRange and withinYRange:
                    mob.takeDamage(app, damage)
                    if tool:
                        tool.curCooldown = tool.attackCooldown

    def eat(self, food):
        self.health += food.foodValue
        if self.health > 10:
            self.health = 10
    
    def updateCanCraft(self, app):
        canCraft = []
        for recipe in recipes:
            if canBeMade(app, recipe):
                canCraft.append(recipe)
        self.canCraft = canCraft
    
    def getAttackDamage(self, app):
        curInv = self.inventory[app.func.selectedInventory]
        if not curInv or not hasattr(curInv, "attackDamage"):
            return 1
        else:
            if curInv.curCooldown > 0:
                return 1
            else:
                return curInv.attackDamage
    
    def getMineLevel(self, app):
        curInv = self.inventory[app.func.selectedInventory]
        if not curInv or not hasattr(curInv, "mineLevel"):
            return self.mineLevel
        else:
            return curInv.mineLevel
    
    def getMineSpeed(self, app):
        curInv = self.inventory[app.func.selectedInventory]
        if not curInv or not hasattr(curInv, "mineSpeed"):
            return self.mineSpeed
        else:
            return curInv.mineSpeed
    
    def breakBlock(self, app, block: Block, drop=True):
        chunk = app.game.getChunk(app, block.chunkInd)
        block = chunk.blocks[(block.x, block.y)]
        item = Item(app, block.type.name, block.x, block.y, block.chunkInd, canPlace=True)
        if block.type.name == "TREE": # breaking whole tree
            # get to bottom of tree
            while ((block.x, block.y - 1) in chunk.blocks and
                chunk.blocks[(block.x, block.y - 1)].type.name == "TREE"):
                block = chunk.blocks[(block.x, block.y - 1)]
            # break every log in the tree
            while block.type.name == "TREE":
                chunk.blocks[(block.x, block.y)] = Air(app, block.x, block.y, block.chunkInd)
                app.game.blocks.remove(block)
                randPos = random.random() * 0.8 - 0.4
                item = Item(app, "LOG", block.x + randPos, block.y,
                            block.chunkInd, canPlace=True,
                            dx=randPos, dy=-0.2)
                chunk.generateAir(app, block) # add air around block
                chunk.ungenerateAir(app, block) # remove air that isn't in contact with a solid block
                chunk.items.add(item)
                if (block.x, block.y + 1) in chunk.blocks:
                    block = chunk.blocks[(block.x, block.y + 1)]
                else:
                    break
        else: # any other type of block
            chunk.blocks[(block.x, block.y)] = Air(app, block.x, block.y, block.chunkInd)
            app.game.blocks.remove(block)
            chunk.generateAir(app, block)
            chunk.ungenerateAir(app, block)
            chunk.items.add(item)
        return item

class Functionality:
    def __init__(self, app):
        self.mouseX = 0
        self.mouseY = 0
        self.hovering = None
        self.hoveringRect = None
        self.debug = False
        self.selectedInventory = 0
        self.canInteract = False
        self.holding = None
        self.goodGraphics = False
        self.keybinds = False
        self.isCrafting = False
        self.craftingPage = 0
        self.craftingSelected = 0
    
    def handleKey(self, app, key):
        """
        FUNC
        """
        if key == K_k or (self.keybinds and key == K_ESCAPE):
            self.keybinds = not self.keybinds
        if self.keybinds:
            return
        if key == K_SLASH:
            self.debug = not self.debug
        if keyIsNumber(key):
            if key != K_0: self.selectedInventory = key - 49
        if key == K_g:
            self.goodGraphics = not self.goodGraphics
        if key == K_MINUS and self.debug:
            rand = random.randint(0, 1)
            chunk = app.game.getChunk(app, app.player.chunk)
            if rand == 0:
                chunk.mobs.add(Mushroom(app, app.player.x, app.player.y))
            else:
                chunk.mobs.add(Slime(app, app.player.x, app.player.y))
        if key == K_e:
            self.isCrafting = not self.isCrafting
        if key == K_RIGHT and self.isCrafting:
            self.craftingSelected += 1
            slot_wh = 24
            totalWidth = app.width * 0.8
            pageLength = int(totalWidth / (slot_wh + 12))
            startInd = app.func.craftingPage * pageLength
            if self.craftingSelected - startInd >= pageLength:
                self.craftingPage += 1
                if self.craftingPage * pageLength >= len(app.player.canCraft):
                    self.craftingPage = len(app.player.canCraft) - 1
            elif self.craftingSelected >= len(app.player.canCraft):
                self.craftingSelected -= 1
        elif key == K_LEFT and self.isCrafting:
            self.craftingSelected -= 1
            slot_wh = 24
            totalWidth = app.width * 0.8
            pageLength = int(totalWidth / (slot_wh + 12))
            startInd = app.func.craftingPage * pageLength
            if self.craftingSelected < 0:
                self.craftingSelected = 0
            elif self.craftingSelected < startInd:
                self.craftingSelected = startInd - 1
                self.craftingPage -= 1
                if self.craftingPage < 0:
                    self.craftingPage = 0
        elif key == K_RETURN or key == KEY_ENTER and self.isCrafting:
            if app.func.craftingSelected < len(app.player.canCraft):
                recipe = app.player.canCraft[app.func.craftingSelected]
                if canBeMade(app, recipe):
                    makeRecipe(app, recipe)
                    app.player.updateCanCraft(app)
                    if self.craftingSelected > len(app.player.canCraft) - 1:
                        self.craftingSelected = len(app.player.canCraft) - 1
                    if self.craftingSelected < 0:
                        self.craftingSelected = 0
        """
        PLAYER
        """
        if pygame.key.get_pressed()[K_LSHIFT]:
            app.player.sneak = True
            slow = 0.5
        elif app.player.dy != 0:
            slow = 0.6
        else:
            app.player.sneak = False
            slow = 1

        if key == K_w and app.player.dy == 0: # JUMP
            app.player.dy -= 0.64 * slow
        
        if key == K_a: # LEFT
            app.player.moveLeft(app, -PLAYER_SPEED * slow)
        elif key == K_d: # RIGHT
            app.player.moveRight(app, PLAYER_SPEED * slow)
        checkBackground(app)
        if key == K_s: # DOWN
            app.player.moveDown(app)

        if key == K_q: # THROW
            app.player.throwItem(app, app.player.inventory[self.selectedInventory],
                                 inInventory=True)

        """
        GAME
        """
        generateChunks(app)
    
    def updateHovering(self, app):
        if self.isCrafting and withinBounds(app.width * 0.1, app.height * 0.76,
                            app.width * 0.9, app.height * 0.90,
                            self.mouseX, self.mouseY):
            self.hovering = None
            self.canInteract = False
            return
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
            
            canBreak = app.player.getMineLevel(app) >= app.func.hovering.mineLevel

            self.canInteract = ((not onPlayer) and distance < 4 and (not isBedrock) and canBreak) or self.debug
        else:
            self.hovering = None
            self.canInteract = False
    
    def handleClick(self, app):
        if self.hovering and self.canInteract:
            if self.hovering.breakable:
                app.player.breakBlock(app, self.hovering)
                    
        self.updateHovering(app)