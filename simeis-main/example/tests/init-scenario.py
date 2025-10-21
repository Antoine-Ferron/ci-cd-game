import random

from ..client import Game

def init_scenario():
    # Create a fake player
    fake_name = str(random.randint(0, 2**64 - 1))
    game = Game(fake_name)

    # Initial status
    initStatus = game.get(f'/player/{game.player["playerId"]}')
    initMoney = initStatus["money"]
    game.init_game()

    # After game init -> Check money again
    # During init, trader, ship and pilot are bought -> The money should decrease
    finalStatus = game.get(f'/player/{game.player["playerId"]}')
    finalMoney = finalStatus["money"]
    print(f"Initial money: {initMoney}, final money: {finalMoney}")
    assert finalMoney != initMoney