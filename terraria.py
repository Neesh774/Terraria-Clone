import cProfile
from pprint import pprint
from time import time
import tkinter
from PIL import Image,ImageTk
from cmu_112_graphics import *
from enum import Enum
import os
from assets.colors import colors
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
        app.images[f[:-4]] = pygame.image.load(os.path.join(ASSETS_DIR, f))
    for f in os.listdir("assets/blocks"):
        if not f.endswith(".png"):
            continue
        app.images[f[:-4]] = pygame.image.load(os.path.join("assets/blocks", f))
    app.game = Game(app)
    app.player = Player(app)
    app.func = Functionality(app)
    app.lastTime = time()
    checkBackground(app)
    app.paused = False
    app.deathScreen = False
    
    app.font = pygame.font.Font("assets/terraria.ttf", 16)
    app.debugFont = pygame.font.Font("assets/terraria.ttf", 12)

def keyPressed(app, event):
    if not app.paused:
        app.func.keys.append(event.key)
    if app.deathScreen:
        app.paused = False
        app.deathScreen = False
        app.player.die(app)
    if event.key == ".":
        app._clearscreen = not app._clearscreen
        print("Clear screen " + ("On" if app._clearscreen else "Off"))

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
            
            block.drawWrapper(app, screen)
            if r == chunk.x and app.func.debug:
                x, _ = getPixFromCoords(app, block.x, block.y)
                pygame.draw.rect(screen, ("red" if chunk.x == app.game.getChunk(app, app.player.chunk).x else "black"),
                                 (x, 0, x + (CHUNK_SIZE * UNIT_WH), app.height))
    
    for item in chunk.items:
        item.draw(app, screen)
    
    for mob in chunk.mobs:
        mob.draw(app, screen)

def drawGame(app, screen: pygame.Surface):
    pygame.draw.rect(screen, getBackgroundColor(app.game.time), (0, 0, app.width, app.height), 0)

    pygame.draw.rect(screen, "#2D404F", (0, app.height * 0.5, app.width, app.height), 0)

    for bgX in app.game.bgX:
        screen.blit(app.background, (bgX, app.height * 0.5))
    
    pygame.draw.rect(screen, "#050505", (0, getPixY(app, GROUND_LEVEL - GRASS_LEVEL - TERRAIN_VARIATION),
                            app.width, app.height), 0)
    
    for chunk in app.game.loaded:
        drawChunk(app, screen, chunk)

def drawPlayer(app, screen: pygame.Surface):
    x = app.width / 2
    y = app.height * 0.6 + UNIT_WH
    screen.blit(app.player.getSprite(), (x, y))

def drawDebug(app, screen: pygame.Surface):
    time = app.font.render(f"G: {app.game.time}", 1, "#9A9A9A")
    pos = time.get_rect()
    pos.center = (5, 10)
    screen.blit(time, pos)

    tps = app.font.render(f'TPS: {round(1 / (time() - app.lastTime), 3)}', "#9A9A9A")
    pos = tps.get_rect()
    pos.center = (5, 30)
    screen.blit(tps, pos)
    
    player = app.font.render(f"Player: {app.player.x}, {app.player.y}", "#9A9A9A")
    pos = player.get_rect()
    pos.center = (5, 50)
    screen.blit(player, pos)

    mouse = app.font.render(f'M: ({app.func.mouseX}, {app.func.mouseY})', "#9A9A9A")
    pos = mouse.get_rect()
    pos.center = (5, 70)
    screen.blit(mouse, pos)

    if app.func.hovering:
        block = app.func.hovering
        if block:
            blockText = app.font.render(f'B: ({block.x}, {block.y}) {block.type.name} {block.chunkInd}', "#9A9A9A")
            pos = blockText.get_rect()
            pos.center = (5, 90)
            screen.blit(blockText, pos)

def drawHotbar(app, screen: pygame.Surface):
    width = 9 * 28 + 40
    itemWidth = int((width - 40) / 9)
    screen.create_rectangle(app.width - width - 8, 12,
                            app.width, 20 + itemWidth,
                            fill="slate gray", width=0)
    for i, item in enumerate(app.player.inventory):
        x = 8 + (i * (itemWidth + 4))
        selected = app.func.selectedInventory == i
        if selected:
            borderWidth = 2
        else:
            borderWidth = 0
        left = app.width - width - 12 + x
        screen.create_rectangle(left, 16,
                                left + itemWidth, 16 + itemWidth, width=borderWidth,
                                fill="#965816", outline="#C79355")
        if item:
            screen.create_image(left + 4 + (itemWidth / 2), 16 + (itemWidth / 2),
                                image=getImage(app, item.name))
        screen.create_text(left + 4, 10, anchor="nw", text=item.count if item else "",
                           font=app.smallFont, fill="#38332F")
    for h in range(0, 10):
        x = app.width - h * 18 - 20
        screen.create_image(x, 64,
                            image=getImage(app, "emptyHeart", (16, 16)))
        if h == app.player.health - 0.5:
            screen.create_image(x, 64,
                                image=getImage(app, "halfHeart", (16, 16)))
        elif h < app.player.health:
            screen.create_image(x, 64,
                                image=getImage(app, "heart", (16, 16)))
    
def drawSettings(app, screen):
    left = app.width * 0.1
    top = app.height * 0.1
    width = app.width * 0.8
    height = app.height * 0.8
    screen.create_rectangle(left, top,
                            left + width, top + height,
                            fill="#C79355", outline="#9D7039", width=3)
    for i, (action, keybind) in enumerate(KEYBINDS.items()):
        cell_height = (height * 0.1) + 2
        row = i * cell_height
        leftCentX = app.width * 0.23
        leftCentY = row + top + (cell_height - 8) / 2
        screen.create_text(leftCentX, leftCentY,
                           text=action, font=("Arial", "16"), fill="#38332F",
                           anchor="nw")
        screen.create_rectangle(app.width * 0.52, row + top + 20,
                                app.width * 0.78, row + top + cell_height,
                                fill="#9D7039", outline="#9D7039", width=3)
        screen.create_text(app.width * 0.65, row + top + 2 + (cell_height / 2),
                           anchor="n",
                           text=keybind, font=("Arial", "12"))

def drawDeath(app, screen):
    screen.create_image(app.width / 2, app.height / 2, image=getImage(app, "options_background", resize=(app.width, app.height)))
    screen.create_text(app.width / 2, app.height * 0.4, width=app.width,
                        text="You Died!", font=("Arial", "32"), fill="#9A9A9A")
    screen.create_text(app.width / 2, app.height * 0.6, width=app.width,
                        text="Press any key to continue", font=("Arial", "22"), fill="#9A9A9A")

def drawCrafting(app, screen):
    slot_wh = 24
    totalWidth = app.width * 0.8
    pageLength = int(totalWidth / (slot_wh + 12))
    startInd = app.func.craftingPage * pageLength
    numCrafts = len(app.player.canCraft)
    screen.create_rectangle(app.width * 0.09, app.height * 0.75,
                            app.width * 0.91, app.height * 0.90,
                            fill="Slategray3", outline="Slategray4", width=4)
    screen.create_text(app.width * 0.12, app.height * 0.78,
                       text=f'Crafting({numCrafts})', font=("Arial", "18", "bold"),
                       fill="Slategray4", width=totalWidth, anchor="w")
    if len(app.player.canCraft) > app.func.craftingSelected and app.player.canCraft[app.func.craftingSelected]:
        selected = app.player.canCraft[app.func.craftingSelected]
        screen.create_text(app.width * 0.89, app.height * 0.78,
                           text=f'{selected["output"].name.capitalize()}(x{selected["output"].count})', font=("Arial", "15", "bold"),
                           width=totalWidth, fill="Slategray4", anchor="e")
    for i in range(pageLength):
        if (startInd + i) >= numCrafts:
            break
        craft = app.player.canCraft[startInd + i]["output"]
        if not craft:
            continue
        if app.func.craftingSelected == startInd + i:
            borderWidth = 2
        else:
            borderWidth = 0
        screen.create_rectangle(app.width * 0.1 + 8 + (i * (slot_wh + 12)) - 4,
                                app.height * 0.85 - (slot_wh / 2) - 4,
                                app.width * 0.1 + 8 + (i * (slot_wh + 12)) + slot_wh + 4,
                                app.height * 0.85 + (slot_wh / 2) + 4,
                                fill="#965816", outline="#CCCCCC", width=borderWidth)
        screen.create_image(app.width * 0.1 + 8 + (i * (slot_wh + 12)) + (slot_wh / 2) + 2,
                            app.height * 0.85 + 2, 
                            image=getImage(app, craft.name, resize=(slot_wh - 2, slot_wh - 2)))
        canCraftNum = numCanCraft(app, app.player.canCraft[startInd + i])
        if not canCraftNum:
            continue
        screen.create_text(app.width * 0.1 + 8 + (i * (slot_wh + 12)),
                            app.height * 0.85 - (slot_wh / 2) + 5,
                            text=canCraftNum * craft.count,
                            font=app.smallFont, fill="#38332F", anchor="w")

def redrawAll(app, screen:pygame.Surface):
    app.entities = []
    if app.deathScreen:
        drawDeath(app, screen)
    else:
        drawGame(app, screen)
        drawPlayer(app, screen)
        if app.func.debug:
            drawDebug(app, screen)
        # for entity in app.entities:
        #     screen.tag_raise(entity)
        # drawHotbar(app, screen)
        # if app.func.keybinds:
        #     drawSettings(app, screen)
        # if app.func.isCrafting:
        #     drawCrafting(app, screen)
    # screen.create_image(app.func.mouseX, app.func.mouseY, image=getImage(app, "cursor"),
    #                     anchor="nw")


def timerFired(app):
    if not app.paused:
        app.lastTime = time()
        """
        PLAYER
        """
        app.player.updateWrapper(app)
        """
        GAME
        """
        app.game.time = round((app.game.time + 0.01) % 23, 2)
        for chunk in app.game.loaded:
            chunk.update(app)

        randomChance = random.randint(0, 50)
        if randomChance == 0:
            app.game.spawnMob(app)
        """
        FUNC
        """
        app.func.handleKeys(app)
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
    
    app = App()
    
    while True:
        app.game.loadChunks(app)
        for event in pygame.event.get():
            if event.type == QUIT:
                return
            elif event.type == KEYDOWN:
                app.func.handleKey(app, event.key)
            elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                mousePressed(app, event.pos)
            elif event.type == MOUSEMOTION:
                mouseMoved(app, event.pos)
            elif event.type == MOUSEBUTTONUP:
                mouseReleased(app)
            elif event.type == WINDOWRESIZED:
                sizeChanged(app)
        redrawAll(app, screen)
        pygame.display.flip()

    
if __name__ == "__main__":
    main()