from items import *
from blocks import *

recipes = [
    {
        "ingredients": {
            "LOG": 1
        },
        "output": InventoryItem("PLANKS", 4, canPlace=True)
    },
    {
        "ingredients": {
            "PLANKS": 2
        },
        "output": InventoryItem("PLATFORM", 1, canPlace=True)
    },
    {
        "ingredients": {
            "PLANKS": 1
        },
        "output": InventoryItem("WALL", 1, canPlace=True)
    },
    {
        "ingredients": {
            "PLANKS": 5
        },
        "output": WoodenPickaxe(1)
    },
    {
        "ingredients": {
            "PLANKS": 4
        },
        "output": WoodenSword(1)
    }
]