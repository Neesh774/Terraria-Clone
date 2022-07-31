from helpers import *

class Block:
    def __init__(self, x, y, block: Blocks, chunkInd, solid = True, breakable = True, color="black"):
        self.x = x
        self.y = y
        self.type = block
        self.chunkInd = chunkInd
        self.solid = solid
        self.breakable = breakable
        self.image = None
        self.color = color
        
    def load(self, app, canvas):
        image = getImage(app, self.type.name)
        if image == None:
            return
        self.image = canvas.create_image(getPixX(app, self.x), getPixY(app, self.y),
                            anchor="nw", image=image)
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
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.AIR, chunkInd, solid=False, breakable=False,
                         color="grey2")
        
class Grass(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.GRASS, chunkInd, color="chartreuse4")

class Dirt(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.DIRT, chunkInd, color="tan4")
        
class Stone(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.STONE, chunkInd, color="seashell4")

class Bedrock(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.BEDROCK, chunkInd, solid=True, breakable=False,
                         color="dark slate gray")