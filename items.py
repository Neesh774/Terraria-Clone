from pprint import pprint
from helpers import *
import inspect

class InventoryItem():
    def __init__(self, name: str, count = 1, canPlace = False,
                 stackMax = STACK_MAX, displayName = None, canUse = False, **kwargs):
        self.name = name
        self.count = count
        self.canPlace = canPlace
        self.stackMax = stackMax
        self.canUse = canUse
        if not displayName:
            self.displayName = name
        else:
            self.displayName = displayName
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    def toItem(self, app, chunk, x, y, canPickUp=True, dx=0, dy=0, count=1):
        args = {}
        for key, val in self.__dict__.items():
                if (key == "type" or key.startswith("_")
                    or key == "rect" or "count" == key or
                    key == "x" or key == "y" or key == "dx" or
                    key == "dy" or key == "chunk" or key == "canPickUp"): continue
                args[key] = val
        return Item(app, x = x, y = y, dx = dx, dy = dy, chunk = chunk, canPickUp=canPickUp, count=(count if count else self.count), **args)
    
    def addToCount(self, count):
        self.count += count
        if self.count < 0:
            self.count = 0
        if self.count > self.stackMax:
            self.count = self.stackMax

    def __eq__(self, other):
        return self.name == other.name
    def __str__(self):
        return f'{self.name}: {self.count}'

class Carrot(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        super().__init__("carrot", count = count)
        self.food = True
        self.foodValue = 1
    def __str__(self):
        return f'Carrot: {self.count}'

class Bread(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        super().__init__("bread", count = count)
        self.food = True
        self.foodValue = 2

class Apple(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        super().__init__("apple", count = count)
        self.food = True
        self.foodValue = 2
        
class WoodenSword(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        self.attackDamage = 2
        self.attackCooldown = 20
        self.curCooldown = 0
        super().__init__("wood_sword", count = count, stackMax = 1, displayName="Wood Sword")

class WoodenPickaxe(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        self.attackDamage = 2
        self.attackCooldown = 20
        self.curCooldown = 0

        self.mineLevel = 2
        self.mineSpeed = 1.5
        super().__init__("wood_pickaxe", count = count, stackMax = 1, displayName="Wood Pickaxe")

class StoneSword(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        self.attackDamage = 3
        self.attackCooldown = 20
        self.curCooldown = 0

        super().__init__("stone_sword", count = count, stackMax = 1, displayName="Stone Sword")
        
class StonePickaxe(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        self.attackDamage = 3
        self.attackCooldown = 20
        self.curCooldown = 0

        self.mineLevel = 3
        self.mineSpeed = 2
        super().__init__("stone_pickaxe", count = count, stackMax = 1, displayName="Stone Pickaxe")

class IronIngot(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
            super().__init__("iron", count = count, displayName="Raw Iron")

class IronSword(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        self.attackDamage = 6
        self.attackCooldown = 15
        self.curCooldown = 0

        super().__init__("iron_sword", count = count, stackMax = 1, displayName="Iron Sword")
        
class IronPickaxe(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        self.attackDamage = 4
        self.attackCooldown = 20
        self.curCooldown = 0

        self.mineLevel = 5
        self.mineSpeed = 3
        super().__init__("iron_pickaxe", count = count, stackMax = 1, displayName="Iron Pickaxe")

class GodItem(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        self.attackDamage = 10
        self.attackCooldown = 0
        self.curCooldown = 0

        self.mineLevel = 10
        self.mineSpeed = 10
        super().__init__("gold_hoe", count = count, stackMax = 1, displayName="God Item")

class BirdEgg(InventoryItem):
    def __init__(self, count = 1, *args, **kwargs):
        super().__init__("egg", count = count, stackMax = 1, displayName="Fat Bird Egg")
    
    def use(self, app):
        app.game.spawnMob(app, "fat_bird")

class Item(Entity):
    def __init__(self, app, name: str, x, y, chunk,  count = 1, canPlace = False,
                 canPickUp = True, dx = 0, dy = 0, inventoryClass=InventoryItem, **kwargs):
        super().__init__(x, y, dx=dx, dy=dy)
        self.name = name
        self.count = count
        self.canPlace = canPlace
        self.chunkInd = chunk
        self.gravityVal = 0.04
        item_wh = int(UNIT_WH * 0.8)
        image = getImage(app, self.name)
        self.image = pygame.transform.scale(image, (item_wh, item_wh))
        self.rect = self.image.get_rect()
        self.rect.x = getPixX(app, x)
        self.rect.y = getPixY(app, y)
        if not canPickUp:
            self.canPickUp = 3
        else:
            self.canPickUp = 0
        self.inventoryClass = inventoryClass
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __str__(self):
        return f'{self.name}: {self.count} ({self.x}, {self.y})'

    def toInventory(self):
        args = {}
        for key, val in self.__dict__.items():
            args[key] = val
        return self.inventoryClass(**args)
    
    def tick(self, app, chunk):
        dist = math.dist((app.player.x, app.player.y), (self.x, self.y))
        if self.canPickUp > 0:
            self.canPickUp = round(self.canPickUp - 0.1, 2)
        if self.canPickUp == 0:
            if dist < 0.5:
                app.player.pickUp(app, self.toInventory())
                self.kill()
            elif dist < 5:
                # tweening to player
                self.x += (app.player.x - self.x) * 0.1
                self.y += (app.player.y - self.y) * 0.1
                self.rect.x = self.x
                self.rect.y = self.y
