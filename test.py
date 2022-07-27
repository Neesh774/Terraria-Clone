from cmu_112_graphics import *

def main():
    runApp(width=500, height=500, mvcCheck=False)

def appStarted(app):
    app._clearCanvas = False
    app.obj = None

def keyPressed(app, event):
    app._canvas.moveto(app.obj, app._canvas.coords(app.obj)[0] + 5, app._canvas.coords(app.obj)[1] + 5)

def redrawAll(app, canvas):
    if not app.obj:
        app.obj = canvas.create_rectangle(10, 10, 40, 40, fill="blue")

main()