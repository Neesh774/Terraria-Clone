import random
import math
from helpers import *
from items import *

class Enemy(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.health = 5
        self.viewRange = 10
        self.attackRange = 1
        self.orient = 1
        self.damage = 0.5
        self.damageCooldown = 0
        
        self.regularAttack = True # different attacks for bosses
        
        self.darkness = 0
    
    def tick(self, app):
        # check if player is in range
        dist = math.dist((self.x, self.y), (app.player.x, app.player.y))

        if dist < self.attackRange and self.damageCooldown == 0 and self.regularAttack: # within attack range
            self.attack(app)
        elif dist < self.viewRange and dist > 1 and self.regularAttack: # move towards player
            self.move(0.01, app.player.x < self.x)
        elif self.regularAttack: # random movement
            randomWillMove = random.randint(0, 50)
            if randomWillMove == 0:
                randomDir = random.randint(0, 1)
                amount = random.randint(0, 4) / 10
                if randomDir == 0:
                    self.moveRight(amount)
                else:
                    self.moveLeft(amount)

        if self.damageCooldown > 0:
            self.damageCooldown -= 0.2
        if self.damageCooldown < 0:
            self.damageCooldown = 0
        
        self.darkness = self.darkestNearbyShadow(app)
        
        if hasattr(self, "mobUpdate"):
            self.mobUpdate(app)
        
        if self.orient == 1:
            self.image = pygame.transform.flip(self.image, True, False)
        
        if self.darkness > 0 and not app.func.debug:
            alpha = int(self.darkness / 4 * 240)
            dark = pygame.Surface((self.rect.width, self.rect.height))
            dark.set_alpha(alpha)
            dark.fill((0, 0, 0))
            self.image.blit(dark, (0, 0))
    
    def moveRight(self, amount = 0.05):
        self.dx += amount
        self.orient = 1
    def moveLeft(self, amount = 0.05):
        self.dx -= amount
        self.orient = -1
    def move(self, amount, left):
        if left:
            self.moveLeft(amount)
        else:
            self.moveRight(amount)

    def attack(self, app, damage = None, attackRange = None):
        if not damage:
            damage = self.damage
        if not attackRange:
            attackRange = self.attackRange
        if math.dist((self.x, self.y), (app.player.x, app.player.y)) > attackRange:
            return
        if app.player.spawnInvincibility > 0:
            return
        if self.damageCooldown > 0:
            return
        app.player.health -= damage
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
        app.player.spawnInvincibility = 50
    
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
    
    def darkestNearbyShadow(self, app):
        darkest = 0
        for x in range(-1, 2):
            for y in range(-1, 2):
                block = getBlockFromCoords(app, self.x + x, self.y + y)
                if block and block.darkness > darkest:
                    darkest = block.darkness
        return darkest

class Mushroom(Enemy):
    def __init__(self, app, x, y):
        super().__init__(x, y)
        self.idle = []
        self.width = 32
        self.height = 32

        idleSprites = app.images["mush-idle"]
        for i in range(14):
            cropped = pygame.Surface((32, 32))
            cropped.blit(idleSprites, (0, 0), (i * 32, 0, (i + 1) * 32, 32))
            cropped.set_alpha(255)
            self.idle.append(cropped)

        self.run = []
        runSprites = app.images["mush-run"]
        for i in range(16):
            cropped = pygame.Surface((32, 32))
            cropped.blit(runSprites, (0, 0), (i * 32, 0, (i + 1) * 32, 32))
            cropped.set_alpha(255)
            self.run.append(cropped)

        self.isHurt = -1
        self.hurt = []
        hurtSprites = app.images["mush-hit"]
        for i in range(5):
            cropped = pygame.Surface((32, 32))
            cropped.blit(hurtSprites, (0, 0), (i * 32, 0, (i + 1) * 32, 32))
            cropped.set_alpha(255)
            self.hurt.append(cropped)
        
        self.spriteIndex = 0
        self.image = self.idle[self.spriteIndex]
        self.rect = self.image.get_rect()
        self.rect.center = (-self.width, -self.height)

    def mobUpdate(self, app):
        if self.isHurt >= 0: # hurt sprites
            self.isHurt += 1
            if self.isHurt == 4:
                self.isHurt = -1
            self.spriteIndex = self.isHurt
            self.image = self.hurt[self.spriteIndex]
        elif self.dx != 0 or self.dy != 0: # run sprites
            self.spriteIndex = (self.spriteIndex + 1) % len(self.run)
            self.image = self.run[self.spriteIndex]
        else: # idle
            self.spriteIndex = (self.spriteIndex + 1) % len(self.idle)
            self.image = self.idle[self.spriteIndex]

    def die(self, app):
        chunk = app.game.getChunk(app, app.game.getChunkIndex(self.x))
        chunk.mobs.remove(self)
        drop = Item(app, "carrot", self.x, self.y, chunk, random.randint(1, 3), dy=-0.5, inventoryClass=Carrot)
        chunk.items.add(drop)

class Slime(Enemy):
    def __init__(self, app, x, y):
        super().__init__(x, y)
        self.health = 10
        self.viewRange = 5
        self.attackRange = 1
        self.damage = 1
        self.idle = []
        self.width = 44
        self.height = 30

        idleSprites = app.images["slime-run"]
        for i in range(10):
            cropped = pygame.Surface((44, 30))
            cropped.blit(idleSprites, (0, 0), (i * 44, 0, (i + 1) * 44, 30))
            cropped.set_alpha(255)
            self.idle.append(cropped)

        self.isHurt = -1
        self.hurt = []
        hurtSprites = app.images["slime-hit"]
        for i in range(5):
            cropped = pygame.Surface((44, 30))
            cropped.blit(hurtSprites, (0, 0), (i * 44, 0, (i + 1) * 44, 30))
            cropped.set_alpha(255)
            self.hurt.append(cropped)
        
        self.spriteIndex = 0
        self.image = self.idle[self.spriteIndex]
        self.rect = self.image.get_rect()
        self.rect.center = (-self.width, -self.height)
    
    def mobUpdate(self, app):
        if self.isHurt >= 0:
            self.isHurt += 1
            if self.isHurt == 4:
                self.isHurt = -1
            self.spriteIndex = self.isHurt
            self.image = self.hurt[self.spriteIndex]
        else:
            self.spriteIndex = (self.spriteIndex + 1) % len(self.idle)
            self.image = self.idle[self.spriteIndex]
    
    def die(self, app):
        chunk = app.game.getChunk(app, app.game.getChunkIndex(self.x))
        chunk.mobs.remove(self)
        drop = Item(app, "carrot", self.x, self.y, chunk, random.randint(1, 3), dy=-0.5, inventoryClass=Carrot)
        chunk.items.add(drop)

class FatBird(Enemy):
    def __init__(self, app, x, y):
        super().__init__(x, y)
        self.health = 40
        self.viewRange = 40
        self.attackRange = 1
        self.dropAttackRange = 4
        self.damage = 8
        self.idle = []
        self.width = 40
        self.height = 48
        self.gravityVal = 0
        
        self.spriteDelay = 5

        idleSprites = app.images["bird-idle"]
        for i in range(8):
            cropped = pygame.Surface((40, 48))
            cropped.blit(idleSprites, (0, 0), (i * 40, 0, (i + 1) * 40, 48))
            cropped.set_alpha(255)
            self.idle.append(cropped)

        self.isHurt = -1
        self.hurt = []
        hurtSprites = app.images["bird-hit"]
        for i in range(5):
            cropped = pygame.Surface((40, 48))
            cropped.blit(hurtSprites, (0, 0), (i * 40, 0, (i + 1) * 40, 48))
            cropped.set_alpha(255)
            self.hurt.append(cropped)
        
        self.fallingSprites = app.images["bird-fall"]
        self.falling = []
        for i in range(4):
            cropped = pygame.Surface((40, 48))
            cropped.blit(self.fallingSprites, (0, 0), (i * 40, 0, (i + 1) * 40, 48))
            cropped.set_alpha(255)
            self.falling.append(cropped)
    
        self.groundSprites = app.images["bird-ground"]
        self.ground = []
        self.onGround = False
        for i in range(4):
            cropped = pygame.Surface((40, 48))
            cropped.blit(self.groundSprites, (0, 0), (i * 40, 0, (i + 1) * 40, 48))
            cropped.set_alpha(255)
            self.ground.append(cropped)
        
        self.spriteIndex = 0
        self.image = self.idle[self.spriteIndex]
        self.rect = self.image.get_rect()
        self.rect.center = (-self.width, -self.height)
        
        self.lastAttack = 0 # how much time since the last attack
        self.rising = False # rising up to the air
        self.regularAttack = False
        self.willAttack = 0 # pausing in the air about to fall
        self.canAttack = 0 # if it can lock onto the player and start falling
        self.isFalling = False # falling
    
        self.damageCooldown = 10
    
    def mobUpdate(self, app):
        
        if self.rising:
            if self.rect.top > 80: # rise
                self.y += 0.5
            elif 1 < abs(self.x - app.player.x) < self.viewRange: # move above player
                self.x += 0.2 if self.rect.centerx < app.player.rect.centerx else -0.2
            elif self.canAttack: # attack
                self.rising = False
                self.willAttack = 50
                self.spriteIndex = 0
        
        if self.lastAttack > 0:
            self.lastAttack -= 1
        else:
            self.lastAttack = 200
            self.rising = True
            self.dy = 0
            self.isFalling = False
            self.canAttack = 50
        
        if self.canAttack > 0:
            self.canAttack -= 1
        
        if self.isFalling and abs(self.y - app.player.y) < self.dropAttackRange:
            self.attack(app, attackRange = self.dropAttackRange)
            self.isFalling = False
        elif self.isFalling:
            self.dy += 0.2
        
        if self.willAttack > 0:
            self.willAttack -= 1
            if self.willAttack == 0:
                self.isFalling = True
        
        if abs(self.y - app.player.y) < self.attackRange and abs(self.x - app.player.x) < self.attackRange:
            self.attack(app, 3)
        
        if self.lastAttack > 0 and not self.rising and not self.isFalling and not self.willAttack:
            self.onGround = True
        
        if self.spriteDelay == 0:
            self.spriteDelay = 5
            if self.isHurt >= 0:
                self.isHurt += 1
                if self.isHurt == 4:
                    self.isHurt = -1
                self.spriteIndex = self.isHurt
                self.image = self.hurt[self.spriteIndex]
            elif self.isFalling:
                self.spriteIndex = (self.spriteIndex + 1) % len(self.falling)
                self.image = self.falling[self.spriteIndex]
                # state = pygame.Surface((self.width, self.height))
                # state.fill((0, 255, 0))
                # state.set_alpha(255)
                # self.image.blit(state, (0, 0), (0, 0, self.width, self.height))
            # elif self.rising:
            #     state = pygame.Surface((self.width, self.height))
            #     state.fill((0, 0, 255))
            #     state.set_alpha(255)
            #     self.image.blit(state, (0, 0), (0, 0, self.width, self.height))
            elif self.onGround:
                self.spriteIndex = (self.spriteIndex + 1)
                if self.spriteIndex == len(self.ground):
                    self.onGround = False
                    self.spriteIndex = 0
                else:
                    self.image = self.ground[self.spriteIndex]
            else:
                self.spriteIndex = (self.spriteIndex + 1) % len(self.idle)
                self.image = self.idle[self.spriteIndex]
                # state = pygame.Surface((self.width, self.height))
                # state.fill((255, 0, 0))
                # state.set_alpha(255)
                # self.image.blit(state, (0, 0), (0, 0, self.width, self.height))
        else:
            self.spriteDelay -= 1
    
    def die(self, app):
        chunk = app.game.getChunk(app, app.game.getChunkIndex(self.x))
        chunk.mobs.remove(self)
        drop = Item(app, "gold_hoe", self.x, self.y, chunk, random.randint(1, 3), dy=-0.5, inventoryClass=GodItem)
        chunk.items.add(drop)