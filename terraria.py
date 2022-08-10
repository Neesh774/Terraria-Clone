from time import time
from enum import Enum
import os
import pygame
from pygame.locals import *
from pygame.key import *

from settings import *
from classes import *
from helpers import *
from recipes import *

###############################################################################
# MVC

def appStarted(app):
    ASSETS_DIR = "assets"
    app.width = 500
    app.height = 500
    app.images = {}
    app.background = pygame.image.load(os.path.join(ASSETS_DIR, 'background.png'))
    for f in os.listdir("assets"):
        if not f.endswith(".png"):
            continue
        image = pygame.image.load(os.path.join(ASSETS_DIR, f))
        image.set_alpha(255)
        app.images[f[:-4]] = image
    
    Game(app)
    app.player = Player(app)
    app.playerSpriteGroup = pygame.sprite.GroupSingle(app.player)
    app.func = Functionality(app)
    app.lastTime = time()
    checkBackground(app)
    app.paused = False
    app.deathScreen = False
    
    app.largeFont = pygame.font.Font("assets/terraria.ttf", 20)
    app.font = pygame.font.Font("assets/terraria.ttf", 16)
    app.smallFont = pygame.font.Font("assets/terraria.ttf", 14)

def keyPressed(app, event):
    if app.deathScreen:
        app.paused = False
        app.deathScreen = False
        app.player.die(app)
    else:
        app.func.handleKey(app, event)

def sizeChanged(app):
    if app.width > 720:
        return app.setSize(720, app.height)
    if app.height > 480:
        return app.setSize(app.width, 480)
    generateChunks(app)
    checkBackground(app)

def mouseMoved(app, event):
    if not app.paused:
        app.func.mouseX = event[0]
        app.func.mouseY = event[1]
        app.func.updateHovering(app)

def mousePressed(app, event):
    if app.func.hovering and app.func.canInteract and not app.paused:
        curInv = app.player.inventory[app.func.selectedInventory]

        if app.func.hovering.breakable:
            app.func.holding = time()

        elif curInv and curInv.canPlace and app.func.hovering.type == Blocks.AIR:
            app.game.placeBlock(app, curInv, app.func.hovering)
        app.func.updateHovering(app)
    elif (app.func.hovering and not app.func.canInteract) or not app.func.hovering:
        curInv = app.player.inventory[app.func.selectedInventory]
        if hasattr(curInv, "food") and curInv.food:
            if app.player.health == 10:
                return
            app.player.eat(curInv)
            curInv.count -= 1
            if curInv.count == 0:
                app.player.inventory[app.func.selectedInventory] = None
        else:
            playerX = getPixX(app, app.player.x)
            right = event[0] > playerX
            app.player.hit(app, right)

def mouseReleased(app):
    if not app.paused: app.func.holding = None

def drawChunk(app, screen: pygame.Surface, chunk: Chunk):
    for r in range(chunk.x, chunk.x + CHUNK_SIZE):
        for b in range(0, BUILD_HEIGHT):
            if (r, b) not in chunk.blocks:
                continue
            block = chunk.blocks[(r, b)]
            
            if r == chunk.x and app.func.debug:
                x, _ = getPixFromCoords(app, block.x, block.y)
                pygame.draw.rect(screen, ("red" if chunk.x == app.game.getChunk(app, app.player.chunk).x else "black"),
                                 (x, 0, (CHUNK_SIZE * UNIT_WH), app.height), 1)
    
    chunk.items.draw(screen)

    chunk.mobs.draw(screen)

def drawGame(app, screen: pygame.Surface):
    pygame.draw.rect(screen, getBackgroundColor(app.game.time), (0, 0, app.width, app.height), 0)

    pygame.draw.rect(screen, "#2D404F", (0, app.height * 0.5, app.width, app.height), 0)

    for bgX in app.game.bgX:
        screen.blit(app.background, (bgX, app.height * 0.2))
    
    pygame.draw.rect(screen, "#050505", (0, getPixY(app, GROUND_LEVEL - GRASS_LEVEL - TERRAIN_VARIATION),
                            app.width, app.height * 2), 0)
    
    for chunk in app.game.loaded:
        drawChunk(app, screen, chunk)
    
    app.game.blocks.draw(screen)

def drawPlayer(app, screen: pygame.Surface):
    x = app.width / 2
    y = app.height * 0.6
    screen.blit(app.player.getSprite(), (x + 0.2, y + 4))

def drawDebug(app, screen: pygame.Surface):
    gameTime = app.font.render(f"G: {app.game.time}", 1, "#9A9A9A")
    pos = gameTime.get_rect()
    pos.left, pos.centery = (5, 15)
    screen.blit(gameTime, pos)

    tps = app.font.render(f'TPS: {round(1 / (time() - app.lastTime), 3)}', 1, "#9A9A9A")
    pos = tps.get_rect()
    pos.left, pos.centery = (5, 35)
    screen.blit(tps, pos)
    
    player = app.font.render(f"Player: {app.player.x}, {app.player.y}", 1, "#9A9A9A")
    pos = player.get_rect()
    pos.left, pos.centery = (5, 55)
    screen.blit(player, pos)

    mouse = app.font.render(f'M: ({app.func.mouseX}, {app.func.mouseY})', 1, "#9A9A9A")
    pos = mouse.get_rect()
    pos.left, pos.centery = (5, 75)
    screen.blit(mouse, pos)

    if app.func.hovering:
        block = app.func.hovering
        if block:
            blockText = app.font.render(f'B: ({block.x}, {block.y}) {block.type.name} {block.chunkInd}', 1, "#9A9A9A")
            pos = blockText.get_rect()
            pos.left, pos.centery = (5, 95)
            screen.blit(blockText, pos)

def drawHotbar(app, screen: pygame.Surface):
    width = 9 * 28 + 40
    itemWidth = int((width - 40) / 9)
    pygame.draw.rect(screen, "#737F8F", (app.width - width - 8, 12,
                            width, itemWidth + 8), 0)
    for i, item in enumerate(app.player.inventory):
        x = 8 + (i * (itemWidth + 4))
        selected = app.func.selectedInventory == i
        left = app.width - width - 12 + x
        pygame.draw.rect(screen, "#965816", (left, 16,
                                itemWidth, itemWidth), 0)
        if selected:
            pygame.draw.rect(screen, "#B4B4B4", (left, 16,
                                itemWidth, itemWidth), 2)
        if item:
            image = pygame.transform.scale(getImage(app, item.name), (itemWidth - 8, itemWidth - 8))
            screen.blit(image, (left + 5, 20))
            count = app.smallFont.render(f"{item.count}", 1, "#38332F")
            pos = count.get_rect()
            pos.left, pos.centery = (left + 2, itemWidth - 4)
            screen.blit(count, pos)

    for h in range(0, 10):
        x = app.width - (h + 1) * (18 + 4)
        emptyHeart = pygame.transform.scale(getImage(app, "emptyHeart"), (16, 16))
        screen.blit(emptyHeart, (x, 64))
        if h == app.player.health - 0.5:
            halfHeart = pygame.transform.scale(getImage(app, "halfHeart"), (16, 16))
            screen.blit(halfHeart, (x, 64))
        elif h < app.player.health:
            heart = pygame.transform.scale(getImage(app, "heart"), (16, 16))
            screen.blit(heart, (x, 64))
    
def drawSettings(app, screen):
    left = app.width * 0.1
    top = app.height * 0.1
    width = app.width * 0.8
    height = app.height * 0.8
    pygame.draw.rect(screen, "#C79355", (left, top, width, height), 0)
    for i, (action, keybind) in enumerate(KEYBINDS.items()):
        cell_height = (height * 0.1) + 2
        row = i * cell_height
        leftCentX = app.width * 0.23
        leftCentY = row + top + (cell_height - 8) / 2

        actionText = app.font.render(action, 1, "#38332F")
        screen.blit(actionText, (leftCentX, leftCentY))

        box = pygame.draw.rect(screen, "#9D7039", (app.width * 0.52, row + top + 20, width * 0.26, cell_height - 20), 0)
        keybindText = app.font.render(keybind, 1, "#38332F")
        pos = keybindText.get_rect()
        pos.centerx, pos.centery = box.center
        screen.blit(keybindText, pos)


def drawDeath(app, screen):
    optionsBg = pygame.transform.scale(getImage(app, "options_background"), (app.width, app.height))
    screen.blit(optionsBg, (0, 0))
    deathText = app.font.render("You Died!", 1, "#9A9A9A")
    pos = deathText.get_rect()
    pos.center = (app.width / 2, app.height / 2)
    screen.blit(deathText, pos)

    restartText = app.font.render("Press any key to continue", 1, "#9A9A9A")
    pos = restartText.get_rect()
    pos.center = (app.width / 2, app.height * 0.6)
    screen.blit(restartText, pos)

def drawCrafting(app, screen):
    slot_wh = 24
    totalWidth = app.width * 0.8
    pageLength = int(totalWidth / (slot_wh + 12))
    startInd = app.func.craftingPage * pageLength
    numCrafts = len(app.player.canCraft)
    pygame.draw.rect(screen, "#767C92", (app.width * 0.09, app.height * 0.75,
                            app.width * 0.82, app.height * 0.15), 0)
    craftHeader = app.largeFont.render(f'Crafting({numCrafts})', 1, "#545B64")
    pos = craftHeader.get_rect()
    pos.left, pos.centery = app.width * 0.10, app.height * 0.78
    screen.blit(craftHeader, pos)
    if len(app.player.canCraft) > app.func.craftingSelected and app.player.canCraft[app.func.craftingSelected]:
        selected = app.player.canCraft[app.func.craftingSelected]
        name = app.font.render(f'{selected["output"].name.capitalize()}(x{selected["output"].count})', 1, '#545B64')
        pos = name.get_rect()
        pos.right, pos.centery = app.width * 0.89, app.height * 0.78
        screen.blit(name, pos)
    for i in range(pageLength):
        if (startInd + i) >= numCrafts:
            break
        craft = app.player.canCraft[startInd + i]["output"]
        if not craft:
            continue
        pygame.draw.rect(screen, "#965816", (app.width * 0.1 + 8 + (i * (slot_wh + 12)) - 4,
                                app.height * 0.85 - (slot_wh / 2) - 4,
                                slot_wh + 8, slot_wh + 8), 0)
        if app.func.craftingSelected == startInd + i:
            pygame.draw.rect(screen, "#B4B4B4", (app.width * 0.1 + 8 + (i * (slot_wh + 12)) - 4,
                                app.height * 0.85 - (slot_wh / 2) - 4,
                                slot_wh + 8, slot_wh + 8), 2)
        image = pygame.transform.scale(getImage(app, craft.name), (slot_wh - 2, slot_wh - 2))
        screen.blit(image, (app.width * 0.1 + 8 + (i * (slot_wh + 12)) + 2,
                            app.height * 0.85 - (slot_wh / 2) + 2))
        canCraftNum = numCanCraft(app, app.player.canCraft[startInd + i])
        if not canCraftNum:
            continue
        count = app.smallFont.render(f'{canCraftNum * craft.count}', 1, '#38332F')
        pos = count.get_rect()
        pos.left, pos.centery = (app.width * 0.1 + 8 + (i * (slot_wh + 12)),
                            app.height * 0.85 - (slot_wh / 2) + 5)
        screen.blit(count, pos)

def redrawAll(app, screen:pygame.Surface):
    if app.deathScreen:
        drawDeath(app, screen)
    else:
        drawGame(app, screen)
        if app.func.debug:
            drawDebug(app, screen)
        drawHotbar(app, screen)
        app.playerSpriteGroup.draw(screen)
        if app.func.keybinds:
            drawSettings(app, screen)
        if app.func.isCrafting:
            drawCrafting(app, screen)
    # screen.create_image(app.func.mouseX, app.func.mouseY, image=getImage(app, "cursor"),
    #                     anchor="nw")


def timerFired(app):
    if not app.paused:
        app.lastTime = time()
        """
        PLAYER
        """
        app.playerSpriteGroup.update(app)
        """
        GAME
        """
        app.game.time = round((app.game.time + 0.01) % 23, 2)
        
        app.game.blocks.update(app)
        
        for chunk in app.game.loaded:
            chunk.update(app)

        # randomChance = random.randint(0, 50)
        # if randomChance == 0:
        #     app.game.spawnMob(app)
        """
        FUNC
        """
        app.func.updateHovering(app)
        if app.func.holding and time() - app.func.holding > 0.2:
            app.func.handleClick(app)
            app.func.holding = None

class App:
    def __init__(self):
        appStarted(self)

def main():
    pygame.init()
    screen = pygame.display.set_mode((500, 500))
    pygame.display.set_caption("Terraria")
    
    pygame.key.set_repeat(150, 30)
    
    app = App()
    
    pygame.time.set_timer(pygame.USEREVENT + 1, 20)
    
    while True: # main event loop
        app.game.loadChunks(app)
        
        for event in pygame.event.get(): # loop through event queue
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN:
                keyPressed(app, event.key)
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                mousePressed(app, event.pos)
            elif event.type == MOUSEMOTION:
                mouseMoved(app, event.pos)
            elif event.type == MOUSEBUTTONUP:
                mouseReleased(app)
            elif event.type == WINDOWRESIZED:
                sizeChanged(app)
            elif event.type == pygame.USEREVENT + 1:
                timerFired(app)
        redrawAll(app, screen)
        pygame.display.flip()
    
if __name__ == "__main__":
    main()