from PIL import Image
import numpy as np
from cmu_112_graphics import *

# Load image, ensure not palettised, and make into Numpy array

def getColors():
    pim = Image.open('image.png').convert('RGB')
    im  = np.array(pim)

    colors = {}

    for x in range(im.shape[1]):
        for y in range(im.shape[0]):
            colors[(x, y)] = im[y, x]
    
    
    width = im.shape[1]
    height = im.shape[0]
    return (colors, width, height)

def appStarted(app):
    app.colors, app.imW, app.imY = getColors()

def redrawAll(app, canvas):
    for x in range(app.width // 2):
        for y in range(app.height // 2):
            color = app.colors[(x, y)]
            color = "#%02x%02x%02x" % (int(color[0]), int(color[1]), int(color[2]))
            canvas.create_rectangle(x * 2, y * 2, (x + 1) * 2, (y + 1) * 2, fill=color)
        
def main():
    pim = Image.open('image.png').convert('RGB')
    im  = np.array(pim)
    runApp(width=im.shape[1]*2, height=im.shape[0]*2)

if __name__ == "__main__":
    main()