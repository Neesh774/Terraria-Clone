from helpers import *

class Item(Entity):
    def __init__(self, name: str, x, y, chunk, count = 1, canPlace = False):
        self.name = name
        self.count = count
        self.canPlace = canPlace
        self.x = x
        self.y = y
        self.chunk = chunk
    def __eq__(self, other):
        return self.name == other.name
    def __str__(self):
        return f'{self.name}: {self.count}'
    
    def update(self, app):
        self.gravity()
    
    def gravity(self):
        self.y += 0.2

class InventoryItem():
    def __init__(self, name: str, count = 1, canPlace = False):
        self.name = name
        self.count = count
        self.canPlace = canPlace
    def __eq__(self, other):
        return self.name == other.name
    def __str__(self):
        return f'{self.name}: {self.count}'
