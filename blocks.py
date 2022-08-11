from helpers import *
from time import time

class Block(pygame.sprite.Sprite):
    def __init__(self, app, x, y, block: Blocks, chunkInd, solid = 1, breakable = True, color="black", mineLevel = 0, **kwargs):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.type = block
        self.chunkInd = chunkInd
        self.solid = solid
        self.breakable = breakable
        if block != Blocks.AIR:
            self.originalImage = pygame.transform.scale(getImage(app, block.name), (UNIT_WH, UNIT_WH))
        self.image = pygame.Surface((UNIT_WH, UNIT_WH))
        self.rect = self.image.get_rect()
        self.rect.center = (-UNIT_WH, UNIT_WH)
        self.color = color
        self.mineLevel = mineLevel
        for key, value in kwargs.items():
            setattr(self, key, value)
        app.game.blocks.add(self)
    
    def update(self, app):
        loadedIndices = [chunk.index for chunk in app.game.loaded]
        if self.chunkInd not in loadedIndices:
            self.kill()
        self.rect.x, self.rect.y = getPixFromCoords(app, self.x, self.y)

        self.image.blit(self.originalImage, (0, 0))

        if app.func.hovering and app.func.hovering.x == self.x and app.func.hovering.y == self.y:
            if not app.func.canInteract:
                outline = "#929292"
            else:
                outline = "#F4AC38"
            if app.func.holding:
                heldTime = time() - app.func.holding
                width = math.ceil(heldTime / 0.2 * 5)
            else:
                width = 1
            pygame.draw.rect(self.image, outline, (0, 0, UNIT_WH, UNIT_WH),
                                width)

    def __str__(self):
        return f"""({self.x}, {self.y}) {self.type.name} C: {self.chunkInd}\n
                    solid={self.solid}
                    breakable={self.breakable}
                    image={self.image}
                """
class Air(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.AIR, chunkInd, solid=0, breakable=False,
                         color="grey2")
        self.image = pygame.Surface((UNIT_WH, UNIT_WH))
        self.image.set_colorkey((0, 0, 0, 0))
        self.originalImage = copy.copy(self.image)
        self.rect = self.image.get_rect()
    
    def update(self, app):
        self.image = pygame.Surface((UNIT_WH, UNIT_WH))
        self.image.set_colorkey((0, 0, 0, 0))
        
        super().update(app)

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
        self.unSolidTimer = 0

    def update(self, app):
        self.image = pygame.Surface((UNIT_WH, UNIT_WH))
        self.image.set_alpha(255)
        
        if self.unSolidTimer > 0:
            self.unSolidTimer -= 1
        else:
            self.solid = 0.5

        super().update(app)
    
    def toggleDensity(self):
        if self.solid == 0.5:
            self.solid = 0
            self.unSolidTimer = 20
        else:
            self.solid = 0.5

class Wall(Block):
    def __init__(self, app, x, y, chunkInd):
        super().__init__(app, x, y, Blocks.WALL, chunkInd, solid=0,
                         color="#A6670E")