from re import I
from helpers import *
import numpy as np

class Block:
    def __init__(self, app, x, y, block: Blocks, chunkInd, solid = 1, breakable = True, color="black", mineLevel = 0, **kwargs):
        self.x = x
        self.y = y
        self.type = block
        self.chunkInd = chunkInd
        self.solid = solid
        self.breakable = breakable
        self.image = None
        self.color = color
        self.mineLevel = mineLevel
        for key, value in kwargs.items():
            setattr(self, key, value)

    def drawWrapper(self, app, screen):
        x, y = getPixFromCoords(app, self.x, self.y)
        if app.func.goodGraphics:
            image = getImage(app, self.type.name)
            if image != None:
                screen.blit(image, (x, y))
        else:
            self.draw(app, screen, x, y)

        if app.func.hovering and app.func.hovering == self:
            if not app.func.canInteract:
                outline = "#929292"
            else:
                outline = "#F4AC38"
            if app.func.holding:
                heldTime = time() - app.func.holding
                width = heldTime / 0.2 * 5
            else:
                width = 1
            pygame.draw.rect(screen, outline (x, y, x + UNIT_WH, y + UNIT_WH),
                                width)
    
    def draw(self, app, screen, x, y):
        pygame.draw.rect(screen, self.color, (x, y, x + UNIT_WH, y + UNIT_WH), 0)

    def __str__(self):
        return f"""({self.x}, {self.y}) {self.type.name} C: {self.chunkInd}\n
                    solid={self.solid}
                    breakable={self.breakable}
                    image={self.image}
                """
    def __eq__(self, other):
        sameCoords = self.x == other.x and self.y == other.y
        sameType = self.type == other.type
        return sameCoords and sameType
class Air(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.AIR, chunkInd, solid=0, breakable=False,
                         color="grey2")
    def draw(self, app, canvas, x, y):
        if belowSurface(app, y):
            canvas.create_rectangle(x, y, x + UNIT_WH, y + UNIT_WH,
                                fill="grey13", width=0)
class Grass(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.GRASS, chunkInd, color="chartreuse4")

class Dirt(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.DIRT, chunkInd, color="tan4")
        
class Stone(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.STONE, chunkInd, color="seashell4")

class Bedrock(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.BEDROCK, chunkInd, solid=1, breakable=False,
                         color="dark slate gray")
    
class Log(Block):
    def __init__(self, app, x, y, chunkInd, natural=False):
        super().__init__(app, x, y, Blocks.LOG, chunkInd,
                         color="LightSalmon4", natural = natural)

class Planks(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.PLANKS, chunkInd, color="LightSalmon3")

class Platform(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.PLATFORM, chunkInd, solid = 0.5,  color="LightSalmon3")
    
    def draw(self, app, canvas, x, y):
        canvas.create_rectangle(x, y, x + UNIT_WH, y + (UNIT_WH / 2),
                                fill=self.color, width=0)
        if belowSurface(app, y):
            canvas.create_rectangle(x, y + (UNIT_WH / 2), x + UNIT_WH, y + UNIT_WH,
                                fill="grey13", width=0)

class Wall(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.WALL, chunkInd, solid=0,
                         color="#A6670E")