from cmu_112_graphics import *
import random
import decimal

CHUNK_SIZE = 32

def roundHalfUp(d):  # helper-fn
    # Round to nearest with ties going away from zero.
    rounding = decimal.ROUND_HALF_UP
    # See other rounding options here:
    # https://docs.python.org/3/library/decimal.html#rounding-modes
    return int(decimal.Decimal(d).to_integral_value(rounding=rounding))

def main():
    runApp(width=500, height=500, mvcCheck=False)

def appStarted(app):
    app.points = generateTerrain(5, 5)
    print(app.points)

def keyPressed(app, event):
    app.points = generateTerrain(5, 5)

def generateTerrain(y1, y2, displace=2, length=0):
    if 2**(length + 1) >= CHUNK_SIZE:
        return [y1, y2]
    displacement = random.randint(0, displace)
    multiply = -1 if random.randint(0, 1) else 1
    midpoint = int(((y1 + y2) / 2) + displacement * multiply)
    length += 1
    return (generateTerrain(y1, midpoint, int(displace * 0.5), length) +
        generateTerrain(midpoint, y2, int(displace * 0.5), length))

def redrawAll(app, canvas):
    unit_width = app.width / len(app.points)
    for i in range(len(app.points)):
        curX = i * unit_width
        curPoint = roundHalfUp(app.points[i]) * 20
        canvas.create_rectangle(curX, app.height - 20 - curPoint, curX + unit_width, app.height - curPoint)

main()