### Project Description

A clone of Terraria that has a different UI and some different aspects of gameplay.

### Structural Plan

Classes:

- Game (Coordinate System, helper functions, manages chunks)
- Chunk (Chunk of terrain)
- Functionality (Game states, event handlers, etc)
- Entity (Collision detection, movement, gravity, etc)
  - Player
  - Mushroom
  - Slime
  - Item (Item that can be picked up)
- InventoryItem (Item within player inventory)
  - Carrot
  - Bread
  - Apple
- Block (Manages one instance of a block)

Separated into `blocks.py`, `classes.py`, `helpers.py`, `items.py`, `terraria.py`, along with `settings.py` and `colors.py` for configuration.

### Algorithmic Plan

- Terrain Generation (Midpoint generation)
- Cave generation (My own design)
- Mob AI (Aggro and wandering)

### Timeline Plan

- TP 2: More items and blocks, reliable mob AI
- TP 3: Better image performance, use actual block sprites

## TP2 Updates

### Technical Updates

- Moved over to Pygame
- Rewrote graphics systems and set up Sprite classes
- Rewrote event handlers and game states
- Using block sprites and images

### Changes to Design

None, other than using images instead of solid colors for blocks.

### TP3 Updates

### Technical Updates

- Game now has lighting, so player can't see blocks that they haven't been within 4 blocks of yet
- Added Andesite and Diorite, which are automatically generated as patches in the ground
- Placed trees in the background, so the player can move through them but still be able to break them
- Added tools to the game, such as Wooden Pickaxe, Sword, and Stone Pickaxe, Sword.
- Used tools to restrict which blocks the player can break
- Sword does more damage than using bare hand
- Tools change how quickly you can break a block

- Added boss: Fat Bird
- Added Item: God Item
- Added Item: Bird Egg
- Added Block: Bird Spawn

### Changes to Design

None, other than lighting

### Version Control Plan

![git](./github.png)

### Citations

[Terrain Gen](https://learn.64bitdragon.com/articles/computer-science/procedural-generation/the-diamond-square-algorithm)

[Textures](https://resourcepack.net/dandelion-resource-pack/)

[Mob Textures](https://pixelfrog-assets.itch.io/pixel-adventure-2)

[Background Image](https://www.deviantart.com/jonata-d/art/Mountain-Sprite-001-706211298)

[Pygame Help](https://kidscancode.org/blog/2016/08/pygame_1-2_working-with-sprites/)

[Pygame Help](https://www.geeksforgeeks.org/pygame-creating-sprites/)

[Pygame Docs](https://www.pygame.org/docs/)

[Pygame Colors](https://riptutorial.com/pygame/example/23788/transparency)
