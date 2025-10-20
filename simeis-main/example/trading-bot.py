# trading_bot.py
import os
import sys
import time
import math

from client import Game, GREEN, RED, GREY

# Paramètres de risque
MAX_CASH_SPEND_RATIO = 0.03
MAX_STOCK_SELL_RATIO = 0.10

# Petit epsilon pour éviter problèmes de comparaison float
EPS = 1e-9

def safe_print(*args, **kwargs):
    print(*args, **kwargs)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)

    name = sys.argv[1]
    game = Game(name)
    game.init_game()

    while True:
        try:
            os.system("clear")
        except Exception:
            pass

        game.disp_status()
        game.go_mine()
        game.disp_status()
        game.go_sell()
        game.upgrade_piloting_member()


        '''
        # Récupère les prix et le taux de frais
        market_prices = game.get_market_prices()
        fee_rate = game.get_fee_rate()  # {'fee_rate': 0.26} par ex

        avg_prices = {
            "Stone": 8.0, "Helium": 8.0,
            "Iron": 32.0, "Ozone": 32.0,
            "Copper": 92.0, "Freon": 92.0,
            "Gold": 160.0, "Oxygen": 160.0,
        }

        # Récupère l'état du joueur (crédits + inventaire station)
        player_status = game.get_player_status()
        credits = player_status["credits"]
        inventory = player_status["inventory"]  # attention: inventaire côté joueur/station

        # Upgrade du trader si on a assez
        if credits > 5000:
            try:
                game.upgrade_trading_member()
            except Exception as e:
                safe_print(f"[!] upgrade_trading_member failed: {e}")

        # Trading uniquement si on n'a pas trop de crédits (comportement existant)
        if credits < 15000:
            safe_print("\n[*] Trading decisions:")
            for resource, avg_price in avg_prices.items():
                # si le marché n'a pas ce produit, skip
                if resource not in market_prices["prices"]:
                    continue

                real_price = float(market_prices["prices"][resource])
                diff_ratio = abs((real_price - avg_price) / avg_price) if avg_price != 0 else 0.0
                trade_strength = min(max(diff_ratio * 2.5, 0.05), 0.6)

                # calcul d'achat maximal en quantité (en respectant le ratio de cash)
                max_spend = credits * MAX_CASH_SPEND_RATIO * trade_strength
                max_buy_qty = 0.0
                if real_price > EPS:
                    max_buy_qty = max_spend / real_price

                # quantité disponible dans l'inventaire local (player_status)
                stock_qty = inventory.get(resource, 0)

                # quantité maximale qu'on peut vendre (ratio de stock * trade_strength)
                max_sell_qty = stock_qty * MAX_STOCK_SELL_RATIO * trade_strength

                # s'assurer que max_sell_qty ne dépasse pas ce qu'on a vraiment
                max_sell_qty = min(max_sell_qty, stock_qty)

                # --- BUY condition (en tenant compte des frais) ---
                try:
                    if real_price < avg_price * (1 - fee_rate["fee_rate"] - 1e-6):
                        safe_print(f"{GREEN} BUY {resource} for {real_price:.3f} | avg={avg_price:.3f} | diff={diff_ratio:.2f} | qty={max_buy_qty:.2f}")
                        if max_buy_qty > 0.0:
                            try:
                                game.buy_resource(resource, max_buy_qty)
                                # après achat, on rafraîchit l'état pour garder l'info à jour
                                player_status = game.get_player_status()
                                credits = player_status["credits"]
                                inventory = player_status["inventory"]
                            except Exception as e:
                                safe_print(f"    [!] buy_resource failed for {resource}: {e}")

                    # --- SELL condition (vendre seulement si on a du stock) ---
                    elif real_price > avg_price * (1 + fee_rate["fee_rate"] + 1e-6):
                        # Récupérer le stock réel en station pour s'assurer (API station)
                        try:
                            station_cargo = game.get(f"/station/{game.sta}")["cargo"]["resources"]
                        except Exception as e:
                            station_cargo = inventory  # fallback
                            safe_print(f"    [!] failed to fetch station cargo, using inventory fallback: {e}")

                        station_stock = station_cargo.get(resource, 0)
                        safe_print(f"{RED} SELL {resource} for {real_price:.3f} | avg={avg_price:.3f} | diff={diff_ratio:.2f} | planned_qty={max_sell_qty:.2f} | station_has={station_stock:.2f}")

                        # Recalc max_sell_qty à partir du stock réel en station
                        max_sell_qty = min(max_sell_qty, station_stock)
                        if max_sell_qty <= 0:
                            safe_print(f"    → nothing to sell for {resource} (station_has={station_stock})")
                        else:
                            try:
                                game.sell_resource(resource, max_sell_qty)
                                # après vente, rafraîchir l'état local
                                player_status = game.get_player_status()
                                credits = player_status["credits"]
                                inventory = player_status["inventory"]
                            except Exception as e:
                                safe_print(f"    [!] sell_resource failed for {resource}: {e}")

                    else:
                        safe_print(f"{GREY} HOLD {resource} at {real_price:.3f} | avg={avg_price:.3f} | diff={diff_ratio:.2f}")

                except Exception as e:
                    # Catch-all pour éviter que le bot plante si un calcul lève une exception
                    safe_print(f"[!] Unexpected error handling {resource}: {e}")

            # affichage de statut et fee_rate
            safe_print("")
            try:
                game.disp_status()
            except Exception as e:
                safe_print(f"[!] disp_status failed: {e}")

            safe_print(f"[*] Current market fee rate: {round(fee_rate['fee_rate']*100, 2)} %")

        else:
            safe_print("[*] Credits >= 15000 — skipping trading this turn")'''
