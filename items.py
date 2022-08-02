from helpers import *

class Item(Entity):
    def __init__(self, name: str, x, y, chunk,  count = 1, canPlace = False,
                 canPickUp = True, dx = 0, dy = 0):
        self.name = name
        self.count = count
        self.canPlace = canPlace
        self.chunkInd = chunk
        self.gravityVal = 0.04
        if not canPickUp:
            self.canPickUp = 3
        else:
            self.canPickUp = 0
        super().__init__(x, y, dx=dx, dy=dy)
    def __eq__(self, other):
        return (self.name == other.name and
            self.x == other.x and
            self.y == other.y)
    def __str__(self):
        return f'{self.name}: {self.count} ({self.x}, {self.y})'
    
    def draw(self, app, canvas):
        item_wh = int(UNIT_WH * 0.8)
        image = getImage(app, self.name, resize=(item_wh, item_wh))
        if image == None:
            return
        canvas.create_image(getPixX(app, self.x), getPixY(app, self.y),
                            anchor="nw", image=image)
    
    def toInventory(self):
        return InventoryItem(self.name, self.count,
                             self.canPlace)
    
    def update(self, app, chunk):
        dist = math.dist((app.player.x, app.player.y), (self.x, self.y))
        if self.canPickUp > 0:
            self.canPickUp = round(self.canPickUp - 0.1, 2)
        if self.canPickUp == 0:
            if dist < 0.5:
                app.player.pickUp(app, InventoryItem(self.name,
                                                        canPlace=self.canPlace, count=self.count))
                chunk.items = [item for item in chunk.items if item != self]
            elif dist < 5:
                # tweening to player
                self.x += (app.player.x - self.x) * 0.1
                self.y += (app.player.y - self.y) * 0.1

class InventoryItem():
    def __init__(self, name: str, count = 1, canPlace = False):
        self.name = name
        self.count = count
        self.canPlace = canPlace

    def toItem(self, chunk, x, y, canPickUp=True, dx=0, dy=0, count=1):
        return Item(self.name, x, y, chunk, count=(count if count else self.count), canPlace=self.canPlace, canPickUp=canPickUp,
                    dx=dx, dy=dy)

    def __eq__(self, other):
        return self.name == other.name
    def __str__(self):
        return f'{self.name}: {self.count}'
