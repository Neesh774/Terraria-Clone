import random
import math
from helpers import *
from items import *

class Enemy(Entity):
    def __init__(self, app, x, y):
        super().__init__(x, y)
        self.health = 5
        self.viewRange = 10
        self.attackRange = 1
        self.orient = 1
        self.damage = 0.5
        self.damageCooldown = 0
    
    def update(self, app):
        # check if player is in range
        dist = math.dist((self.x, self.y), (app.player.x, app.player.y))

        if dist < self.attackRange and self.damageCooldown == 0: # within attack range
            self.attack(app)
        elif dist < self.viewRange and dist > 1: # move towards player
            self.move(0.05, app.player.x < self.x)
        else:
            randomWillMove = random.randint(0, 50)
            if randomWillMove == 0:
                randomDir = random.randint(0, 1)
                amount = random.randint(0, 7) / 10
                if randomDir == 0:
                    self.moveRight(amount)
                else:
                    self.moveLeft(amount)

        if self.damageCooldown > 0:
            self.damageCooldown -= 0.2
        if self.damageCooldown < 0:
            self.damageCooldown = 0
        
        if hasattr(self, "mobUpdate"):
            self.mobUpdate()
    
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

class Mushroom(Enemy):
    def __init__(self, app, x, y):
        super().__init__(app, x, y)
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
    
    def draw(self, app, canvas):
        x = getPixX(app, self.x)
        y = getPixY(app, self.y)
        if self.isHurt >= 0:
            sprite = self.hurt[self.spriteIndex]
        elif self.dx != 0 or self.dy != 0:
            sprite = self.run[self.spriteIndex]
        else:
            sprite = self.idle[self.spriteIndex]
        if self.orient == 1:
            sprite = sprite.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        canvas.create_image(x, y, image=ImageTk.PhotoImage(sprite))

    def mobUpdate(self):
        if self.isHurt >= 0:
            self.isHurt += 1
            if self.isHurt == 4:
                self.isHurt = -1
            self.spriteIndex = self.isHurt
        elif self.dx != 0 or self.dy != 0:
            self.spriteIndex = (self.spriteIndex + 1) % len(self.run)
        else:
            self.spriteIndex = (self.spriteIndex + 1) % len(self.idle)
    
    def die(self, app):
        chunk = app.game.getChunk(app, app.game.getChunkIndex(self.x))
        chunk.mobs.remove(self)
        drop = Item("carrot", self.x, self.y, chunk, random.randint(1, 3), dy=-0.5, inventoryClass=Carrot)
        chunk.items.append(drop)

class Slime(Enemy):
    def __init__(self, app, x, y):
        super().__init__(app, x, y)
        self.health = 10
        self.viewRange = 5
        self.attackRange = 1
        self.damage = 1
        self.idle = []
        self.width = 44
        self.height = 30
        idleSprites = app.images["slime-run"]
        for i in range(10):
            sprite = idleSprites.crop((44 * i, 0, 44 * (i + 1), 30))
            self.idle.append(sprite)
        self.spriteIndex = 0
        self.isHurt = -1
        self.hurt = []
        hurtSprites = app.images["slime-hit"]
        for i in range(5):
            sprite = hurtSprites.crop((44 * i, 0, 44 * (i + 1), 30))
            self.hurt.append(sprite)
    
    def mobUpdate(self):
        if self.isHurt >= 0:
            self.isHurt += 1
            if self.isHurt == 4:
                self.isHurt = -1
            self.spriteIndex = self.isHurt
        else:
            self.spriteIndex = (self.spriteIndex + 1) % len(self.idle)
    
    def draw(self, app, canvas):
        x = getPixX(app, self.x)
        y = getPixY(app, self.y)
        if self.isHurt >= 0:
            sprite = self.hurt[self.spriteIndex]
        else:
            sprite = self.idle[self.spriteIndex]
        if self.orient == 1:
            sprite = sprite.transpose(method=Image.Transpose.FLIP_LEFT_RIGHT)
        app.entities.append(canvas.create_image(x, y, image=ImageTk.PhotoImage(sprite)))
    
    def die(self, app):
        chunk = app.game.getChunk(app, app.game.getChunkIndex(self.x))
        chunk.mobs.remove(self)
        drop = Item("carrot", self.x, self.y, chunk, random.randint(1, 3), dy=-0.5, inventoryClass=Carrot)
        chunk.items.append(drop)