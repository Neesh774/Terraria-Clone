import cProfile
from pprint import pprint
from time import time
import tkinter
from PIL import Image,ImageTk
from cmu_112_graphics import *
from enum import Enum
import os
from assets.colors import colors

from settings import *
from classes import *
from helpers import *
from recipes import *

###############################################################################
# MVC

def appStarted(app):
    app.images = {}
    app.background = ImageTk.PhotoImage(Image.open("assets/background.png"))
    for f in os.listdir("assets"):
        if not f.endswith(".png"):
            continue
        app.images[f[:-4]] = Image.open("assets/" + f)
    for f in os.listdir("assets/blocks"):
        if not f.endswith(".png"):
            continue
        app.images[f[:-4]] = Image.open("assets/blocks/" + f).resize((UNIT_WH, UNIT_WH))
    app.game = Game(app)
    app.player = Player(app)
    # app.game.loadChunks(app)
    app.func = Functionality(app)
    app.lastTime = time()
    checkBackground(app)
    app.setPosition(600, 200)
    app.paused = False
    app.deathScreen = False
    
    app.boldFont = ("Farisi", 16, "bold")
    app.smallFont = ("Farisi", 16)
    app.debugFont = ("Arial", 12)

def keyPressed(app, event):
    if not app.paused:
        app.func.keys.append(event.key)
    if app.deathScreen:
        app.paused = False
        app.deathScreen = False
        app.player.die(app)
    if event.key == ".":
        app._clearCanvas = not app._clearCanvas
        print("Clear Canvas " + ("On" if app._clearCanvas else "Off"))

def sizeChanged(app):
    if app.width > 720:
        return app.setSize(720, app.height)
    if app.height > 480:
        return app.setSize(app.width, 480)
    generateChunks(app)
    checkBackground(app)

def mouseMoved(app, event):
    if not app.paused:
        app.func.mouseX = event.x
        app.func.mouseY = event.y
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
            right = event.x > playerX
            app.player.hit(app, right)

def mouseReleased(app, event):
    if not app.paused: app.func.holding = None

def drawChunk(app, canvas: tkinter.Canvas, chunk: Chunk):
    for r in range(chunk.x, chunk.x + CHUNK_SIZE):
        for b in range(0, BUILD_HEIGHT):
            if (r, b) not in chunk.blocks:
                continue
            block = chunk.blocks[(r, b)]
            
            block.drawWrapper(app, canvas)
            if r == chunk.x and app.func.debug:
                x, _ = getPixFromCoords(app, block.x, block.y)
                canvas.create_rectangle(x, 0, x + (CHUNK_SIZE * UNIT_WH), app.height,
                            outline=("red" if chunk.x == app.game.getChunk(app, app.player.chunk).x else "black"))
    
    for item in chunk.items:
        item.draw(app, canvas)
    
    for mob in chunk.mobs:
        mob.draw(app, canvas)

def drawGame(app, canvas: tkinter.Canvas):
    canvas.create_rectangle(0, 0, app.width, app.height,
                            fill=getBackgroundColor(app.game.time))
    canvas.create_rectangle(0, app.height * 0.5, app.width, app.height,
                            fill="#2D404F")

    for bgX in app.game.bgX:
        canvas.create_image(bgX, app.height * 0.5, image=app.background, anchor="e")

    for chunk in app.game.loaded:
        drawChunk(app, canvas, chunk)
    if app.func.hoveringRect:
        canvas.lift(app.func.hoveringRect)

def drawPlayer(app, canvas: tkinter.Canvas):
    x = app.width / 2
    y = app.height * 0.6 + UNIT_WH
    canvas.create_image(x, y, image=app.player.getSprite(), anchor="sw")

def drawDebug(app, canvas: tkinter.Canvas):
    canvas.create_text(5, 10, text=f"G: {app.game.time}", anchor="nw",
                       font=app.debugFont, fill="#9A9A9A")
    canvas.create_text(5, 30, text=f'TPS: {round(1 / (time() - app.lastTime), 3)}',
                       anchor="w", font=app.debugFont, fill="#9A9A9A")
    canvas.create_text(5, 50,
                       text=f'P: ({round(app.player.x, 4)}, {round(app.player.y, 4)}) ({round(app.player.dx, 4)}, {round(app.player.dy, 4)}) {app.player.chunk} {app.player.falling}',
                       fill="#9A9A9A",font=app.debugFont, anchor="w")
    canvas.create_text(5, 70,
                        text=f'M: ({app.func.mouseX}, {app.func.mouseY})',
                        fill="#9A9A9A",font=app.debugFont, anchor="w")
    if app.func.hovering:
        block = app.func.hovering
        if block:
            canvas.create_text(5, 90,
                       text=f'B: ({block.x}, {block.y}) {block.type.name} {block.chunkInd}',
                       fill="#9A9A9A",font=app.debugFont, anchor="w")

def drawHotbar(app, canvas: tkinter.Canvas):
    width = 9 * 28 + 40
    itemWidth = int((width - 40) / 9)
    canvas.create_rectangle(app.width - width - 8, 12,
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
        canvas.create_rectangle(left, 16,
                                left + itemWidth, 16 + itemWidth, width=borderWidth,
                                fill="#965816", outline="#C79355")
        if item:
            canvas.create_image(left + 4 + (itemWidth / 2), 16 + (itemWidth / 2),
                                image=getImage(app, item.name))
        canvas.create_text(left + 4, 10, anchor="nw", text=item.count if item else "",
                           font=app.smallFont, fill="#38332F")
    for h in range(0, 10):
        x = app.width - h * 18 - 20
        canvas.create_image(x, 64,
                            image=getImage(app, "emptyHeart", (16, 16)))
        if h == app.player.health - 0.5:
            canvas.create_image(x, 64,
                                image=getImage(app, "halfHeart", (16, 16)))
        elif h < app.player.health:
            canvas.create_image(x, 64,
                                image=getImage(app, "heart", (16, 16)))
    
def drawSettings(app, canvas):
    left = app.width * 0.1
    top = app.height * 0.1
    width = app.width * 0.8
    height = app.height * 0.8
    canvas.create_rectangle(left, top,
                            left + width, top + height,
                            fill="#C79355", outline="#9D7039", width=3)
    for i, (action, keybind) in enumerate(KEYBINDS.items()):
        cell_height = (height * 0.1) + 2
        row = i * cell_height
        leftCentX = app.width * 0.23
        leftCentY = row + top + (cell_height - 8) / 2
        canvas.create_text(leftCentX, leftCentY,
                           text=action, font=("Arial", "16"), fill="#38332F",
                           anchor="nw")
        canvas.create_rectangle(app.width * 0.52, row + top + 20,
                                app.width * 0.78, row + top + cell_height,
                                fill="#9D7039", outline="#9D7039", width=3)
        canvas.create_text(app.width * 0.65, row + top + 2 + (cell_height / 2),
                           anchor="n",
                           text=keybind, font=("Arial", "12"))

def drawDeath(app, canvas):
    canvas.create_image(app.width / 2, app.height / 2, image=getImage(app, "options_background", resize=(app.width, app.height)))
    canvas.create_text(app.width / 2, app.height * 0.4, width=app.width,
                        text="You Died!", font=("Arial", "32"), fill="#9A9A9A")
    canvas.create_text(app.width / 2, app.height * 0.6, width=app.width,
                        text="Press any key to continue", font=("Arial", "22"), fill="#9A9A9A")

def drawCrafting(app, canvas):
    slot_wh = 24
    totalWidth = app.width * 0.8
    pageLength = int(totalWidth / (slot_wh + 12))
    startInd = app.func.craftingPage * pageLength
    numCrafts = len(app.player.canCraft)
    canvas.create_rectangle(app.width * 0.09, app.height * 0.75,
                            app.width * 0.91, app.height * 0.90,
                            fill="Slategray3", outline="Slategray4", width=4)
    canvas.create_text(app.width * 0.12, app.height * 0.78,
                       text=f'Crafting({numCrafts})', font=("Arial", "18", "bold"),
                       fill="Slategray4", width=totalWidth, anchor="w")
    if len(app.player.canCraft) > app.func.craftingSelected and app.player.canCraft[app.func.craftingSelected]:
        selected = app.player.canCraft[app.func.craftingSelected]
        canvas.create_text(app.width * 0.89, app.height * 0.78,
                           text=f'{selected["output"].name.capitalize()}(x{selected["output"].count})', font=("Arial", "15", "bold"),
                           width=totalWidth, fill="Slategray4", anchor="e")
    for i in range(pageLength):
        if (startInd + i) >= numCrafts:
            break
        craft = app.player.canCraft[startInd + i]["output"]
        if app.func.craftingSelected == startInd + i:
            borderWidth = 2
        else:
            borderWidth = 0
        canvas.create_rectangle(app.width * 0.1 + 8 + (i * (slot_wh + 12)) - 4,
                                app.height * 0.85 - (slot_wh / 2) - 4,
                                app.width * 0.1 + 8 + (i * (slot_wh + 12)) + slot_wh + 4,
                                app.height * 0.85 + (slot_wh / 2) + 4,
                                fill="#965816", outline="#CCCCCC", width=borderWidth)
        canvas.create_image(app.width * 0.1 + 8 + (i * (slot_wh + 12)) + (slot_wh / 2) + 2,
                            app.height * 0.85 + 2, 
                            image=getImage(app, craft.name, resize=(slot_wh - 2, slot_wh - 2)))
        canCraftNum = numCanCraft(app, app.player.canCraft[startInd + i])
        canvas.create_text(app.width * 0.1 + 8 + (i * (slot_wh + 12)),
                            app.height * 0.85 - (slot_wh / 2) + 5,
                            text=canCraftNum * craft.count,
                            font=app.smallFont, fill="#38332F", anchor="w")

def redrawAll(app, canvas:tkinter.Canvas):
    app.entities = []
    if app.deathScreen:
        drawDeath(app, canvas)
    else:
        app.game.loadChunks(app, canvas)
        drawGame(app, canvas)
        drawPlayer(app, canvas)
        if app.func.debug:
            drawDebug(app, canvas)
        for entity in app.entities:
            canvas.tag_raise(entity)
        drawHotbar(app, canvas)
        if app.func.keybinds:
            drawSettings(app, canvas)
        if app.func.isCrafting:
            drawCrafting(app, canvas)
    canvas.create_image(app.func.mouseX, app.func.mouseY, image=getImage(app, "cursor"),
                        anchor="nw")


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

def main():
    runApp(width=500, height=500, title="Terraria", mvcCheck=False)
    
if __name__ == "__main__":
    main()