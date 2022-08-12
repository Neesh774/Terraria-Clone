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
        
        self.darkness = 0
    
    def tick(self, app):
        # check if player is in range
        dist = math.dist((self.x, self.y), (app.player.x, app.player.y))

        if dist < self.attackRange and self.damageCooldown == 0: # within attack range
            self.attack(app)
        elif dist < self.viewRange and dist > 1: # move towards player
            self.move(0.01, app.player.x < self.x)
        else: # random movement
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

    def attack(self, app):
        if app.player.spawnInvincibility > 0:
            return
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