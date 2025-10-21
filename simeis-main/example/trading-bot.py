import os
import sys
import time
import math
from datetime import datetime
import sys

#test 
from client import Game, GREEN, RED, GREY

# Maximum amount of cash to spend per round
MAX_CASH_SPEND_RATIO = 0.03
# Maximum amount of stock to sell per round
MAX_STOCK_SELL_RATIO = 0.10

EPS = 1e-9

def safe_print(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    name = sys.argv[1]
    game = Game(name)
    game.init_game()

    total_profit = 0.0
    loop_count = 0

    while True:
        # Refresh terminal
        loop_count += 1
        try:
            os.system("clear")
        except Exception:
            pass

        # Show iteration
        safe_print("\n" + "=" * 40)
        safe_print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Trading round #{loop_count}")
        safe_print("=" * 40)

        # Market data + fees
        market_prices = game.get_market_prices()
        fee_rate = game.get_fee_rate()

        # Average prices
        avg_prices = {
            "Stone": 8.0, "Helium": 8.0,
            "Iron": 32.0, "Ozone": 32.0,
            "Copper": 92.0, "Freon": 92.0,
            "Gold": 160.0, "Oxygen": 160.0,
        }

        # Player status
        player_status = game.get_player_status()
        credits = player_status["credits"]
        inventory = player_status["inventory"]

        # Station stock
        try:
            station_data = game.get(f"/station/{game.sta}")
            station_cargo = station_data["cargo"]["resources"]
        except Exception as e:
            station_cargo = inventory
            safe_print(f"[!] failed to fetch station cargo: {e}")

        # Player status display
        safe_print(f"Trader: {name} | Credits: {credits:,.2f} | Total Profit: {total_profit:+,.2f}")
        safe_print(f"Market Fee: {fee_rate['fee_rate']*100:.2f}%")
        safe_print("-" * 60)
        safe_print("[*] Trading decisions:")

        # Auto-upgrade if enough credits
        if credits > 2500:
            try:
                game.upgrade_trading_member()
            except Exception as e:
                safe_print(f"[!] upgrade_trading_member failed: {e}")

        # Main loop
        for resource, avg_price in avg_prices.items():

            # Market data
            real_price = float(market_prices["prices"][resource])
            diff_ratio = abs((real_price - avg_price) / avg_price) if avg_price != 0 else 0.0
            trade_strength = min(max(diff_ratio * 2.5, 0.05), 0.6)
            max_spend = credits * MAX_CASH_SPEND_RATIO * trade_strength
            max_buy_qty = max_spend / real_price if real_price > EPS else 0.0
            have_qty = station_cargo.get(resource, 0)

            try:
                # BUY Section
                isCreditAbove1000 = credits > 1000
                if real_price < avg_price * (1 - 0.15):
                    safe_print(f"{GREEN if isCreditAbove1000 else GREY} {GREEN} BUY  {resource:<7} for {real_price:8.3f} | avg={avg_price:6.3f} | qty={max_buy_qty:8.2f} | have={have_qty:8.2f}")
                    if isCreditAbove1000 and max_buy_qty > 0.0:
                        try:
                            game.buy_resource(resource, max_buy_qty)
                            cost = real_price * max_buy_qty * (1 + fee_rate["fee_rate"])
                            total_profit -= cost
                        except Exception as e:
                            safe_print(f"    [!] buy_resource failed: {e}")

                # SELL Section
                elif real_price > avg_price * (1 + 0.15):
                    station_stock = station_cargo.get(resource, 0)
                    price_diff = (real_price / avg_price) - 1
                    k = 10.0
                    min_threshold = fee_rate["fee_rate"] + 0.05
                    sell_ratio = 1 - math.exp(-k * (price_diff - min_threshold)) if price_diff > min_threshold else 0.0
                    sell_ratio = min(max(sell_ratio, 0.0), 1.0)
                    max_sell_qty = station_stock * sell_ratio

                    safe_print(f"{RED if max_sell_qty else GREY} {RED} SELL {resource:<7} for {real_price:8.3f} | avg={avg_price:6.3f} | have={station_stock:8.2f}")

                    if max_sell_qty > 0:
                        try:
                            game.sell_resource(resource, max_sell_qty)
                            revenue = real_price * max_sell_qty * (1 - fee_rate["fee_rate"])
                            total_profit += revenue
                        except Exception as e:
                            safe_print(f"    [!] sell_resource failed: {e}")

                # HOLD Section
                else:
                    safe_print(f"{GREY} {GREY} HOLD {resource:<7} at {real_price:8.3f} | avg={avg_price:6.3f} | diff={diff_ratio:5.2f} | have={have_qty:8.2f}")

            except Exception as e:
                safe_print(f"[!] Unexpected error handling {resource}: {e}")

        # Summary
        safe_print("-" * 60)
        safe_print(f"Current profit: {total_profit:+,.2f} credits | Fee rate: {fee_rate['fee_rate']*100:.2f}%")

