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
    },
    {
        "ingredients": {
            "PLANKS": 2,
            "STONE": 2
        },
        "output": StoneSword(1)
    },
    {
        "ingredients": {
            "PLANKS": 2,
            "STONE": 3
        },
        "output": StonePickaxe(1)
    },
    {
        "ingredients": {
            "IRON_ORE": 1
        },
        "output": IronIngot(1)
    },
    {
        "ingredients": {
            "iron": 3,
            "PLANKS": 2
        },
        "output": IronPickaxe(1)
    },
    {
        "ingredients": {
            "iron": 2,
            "PLANKS": 2
        },
        "output": IronSword(1)
    }
]