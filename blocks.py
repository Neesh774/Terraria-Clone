from helpers import *

class Block:
    def __init__(self, x, y, block: Blocks, chunkInd, solid = True, breakable = True):
        self.x = x
        self.y = y
        self.type = block
        self.chunkInd = chunkInd
        self.solid = solid
        self.breakable = breakable
    def __str__(self):
        return f"""({self.x}, {self.y}) {self.type.name} C: {self.chunkInd}\n
                    solid={self.solid}
                    breakable={self.breakable}
                """
    
class Air(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.AIR, chunkInd, solid=False, breakable=False)
        
class Grass(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.GRASS, chunkInd)

class Dirt(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.DIRT, chunkInd)
        
class Stone(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.STONE, chunkInd)

class Bedrock(Block):
    def __init__(self, x, y, chunkInd):
        super().__init__(x, y, Blocks.BEDROCK, chunkInd, solid=True, breakable=False)