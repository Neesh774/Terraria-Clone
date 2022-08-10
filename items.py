from helpers import *

class InventoryItem():
    def __init__(self, name: str, count = 1, canPlace = False):
        self.name = name
        self.count = count
        self.canPlace = canPlace

    def toItem(self, app, chunk, x, y, canPickUp=True, dx=0, dy=0, count=1):
        return Item(app, self.name, x, y, chunk, count=(count if count else self.count), canPlace=self.canPlace, canPickUp=canPickUp,
                    dx=dx, dy=dy)
    
    def addToCount(self, count):
        self.count += count
        if self.count < 0:
            self.count = 0
        if self.count > STACK_MAX:
            self.count = STACK_MAX

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

class Item(Entity, pygame.sprite.Sprite):
    def __init__(self, app, name: str, x, y, chunk,  count = 1, canPlace = False,
                 canPickUp = True, dx = 0, dy = 0, inventoryClass=InventoryItem):
        pygame.sprite.Sprite.__init__(self)
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
        super().__init__(x, y, dx=dx, dy=dy)
    # def __eq__(self, other):
    #     return (self.name == other.name and
    #         self.x == other.x and
    #         self.y == other.y)
    def __str__(self):
        return f'{self.name}: {self.count} ({self.x}, {self.y})'

    def toInventory(self):
        return self.inventoryClass(name=self.name, count=self.count,
                                canPlace=self.canPlace)
    
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
