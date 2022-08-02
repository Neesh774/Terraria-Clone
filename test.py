from cmu_112_graphics import *
import random
import decimal

def roundHalfUp(d):  # helper-fn
    # Round to nearest with ties going away from zero.
    rounding = decimal.ROUND_HALF_UP
    # See other rounding options here:
    # https://docs.python.org/3/library/decimal.html#rounding-modes
    return int(decimal.Decimal(d).to_integral_value(rounding=rounding))

def main():
    runApp(width=500, height=500, mvcCheck=False)

# def appStarted(app):
#     pass


# def generateCaves():
#     pass

# def generateEmptyCaveMap():
    

# def redrawAll(app, canvas):
#     pass

# main()