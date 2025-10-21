# clien
import os
import sys
import math
import time
import json
import string
import urllib.request
import urllib.parse

PORT = 8080
URL = f"http://127.0.0.1:{PORT}"

# Colors
GREEN = "\033[42m  \033[0m"  # GREEN square
RED = "\033[41m  \033[0m"    # RED square
GREY = "\033[47m  \033[0m"   # GREY square


class SimeisError(Exception):
    pass

def get_dist(a, b):
    return math.sqrt(((a[0] - b[0]) ** 2) + ((a[1] - b[1]) ** 2) + ((a[2] - b[2]) ** 2))

def check_has(alld, key, *req):
    alltypes = [c[key] for c in alld.values()]
    return all([k in alltypes for k in req])

class Game:
    def __init__(self, username):
        assert self.get("/ping")["ping"] == "pong"
        print("[*] Connection to server OK")
        self.setup_player(username)

        self.pid = self.player["playerId"]
        self.sid = None
        self.sta = None

    def get(self, path, **qry):
        if hasattr(self, "player"):
            qry["key"] = self.player["key"]

        tail = ""
        if len(qry) > 0:
            tail += "?"
            tail += "&".join([
                "{}={}".format(k, urllib.parse.quote(str(v))) for k, v in qry.items()
            ])

        qry = f"{URL}{path}{tail}"
        reply = urllib.request.urlopen(qry, timeout=2)
        data = json.loads(reply.read().decode())
        err = data.pop("error")
        if err != "ok":
            raise SimeisError(err)
        return data

    def disp_status(self):
        status = self.get("/player/" + str(self.pid))
        print("[*] Current status: {} credits, costs: {}, time left before lost: {} secs".format(
            round(status["money"], 2),
            round(status["costs"], 2),
            int(status["money"] / status["costs"]) if status["costs"] > 0 else -1
        ))

    def get_player_status(self):
        status = self.get("/player/" + str(self.pid))
        money = round(status.get("money", 0.0), 2)
        costs = round(status.get("costs", 0.0), 2)
        inventory = status.get("inventory", {}) or {}
        time_left = int(money / costs) if costs > 0 else -1
        return {
            "credits": money,
            "costs": costs,
            "time_left": time_left,
            "inventory": inventory
        }

    def setup_player(self, username, force_register=False):
        username = "".join([c for c in username if c in string.ascii_letters + string.digits]).lower()
        if force_register or not os.path.isfile(f"./{username}.json"):
            player = self.get(f"/player/new/{username}")
            with open(f"./{username}.json", "w") as f:
                json.dump(player, f, indent=2)
            print(f"[*] Created player {username}")
            self.player = player
        else:
            with open(f"./{username}.json", "r") as f:
                self.player = json.load(f)
            print(f"[*] Loaded data for player {username}")

        try:
            player = self.get("/player/{}".format(self.player["playerId"]))
        except SimeisError:
            return self.setup_player(username, force_register=True)

        if player["money"] <= 0.0:
            print("!!! Player already lost, please restart the server to reset the game")
            sys.exit(0)

    def buy_first_ship(self, sta):
        available = self.get(f"/station/{sta}/shipyard/list")["ships"]
        cheapest = sorted(available, key=lambda ship: ship["price"])[0]
        print("[*] Purchasing first ship for {} credits".format(cheapest["price"]))
        self.get(f"/station/{sta}/shipyard/buy/" + str(cheapest["id"]))

    def hire_first_pilot(self, sta, ship):
        pilot = self.get(f"/station/{sta}/crew/hire/pilot")["id"]
        self.get(f"/station/{sta}/crew/assign/{pilot}/{ship}/pilot")

    def hire_first_trader(self, sta):
        trader = self.get(f"/station/{sta}/crew/hire/trader")["id"]
        self.get(f"/station/{sta}/crew/assign/{trader}/trading")

    def init_game(self):
        status = self.get(f"/player/{self.pid}")
        self.sta = list(status["stations"].keys())[0]
        station = self.get(f"/station/{self.sta}")

        if not check_has(station["crew"], "member_type", "Trader"):
            self.hire_first_trader(self.sta)
            print("[*] Hired a trader at station", self.sta)

        if len(status["ships"]) == 0:
            self.buy_first_ship(self.sta)
            status = self.get(f"/player/{self.pid}")
        ship = status["ships"][0]
        self.sid = ship["id"]

        if not check_has(ship["crew"], "member_type", "Pilot"):
            self.hire_first_pilot(self.sta, self.sid)
            print("[*] Hired pilot for ship", self.sid)

        print("[*] Game initialized successfully")

    def get_market_prices(self):
        return self.get(f"/market/prices")

    def get_fee_rate(self):
        fee_rate = self.get(f"/market/{self.sta}/fee_rate")
        return fee_rate

    def buy_resource(self, resource, amount):
        self.get(f"/market/{self.sta}/buy/{resource}/{amount}")

    def sell_resource(self, resource, amount):
        self.get(f"/market/{self.sta}/sell/{resource}/{amount}")

    def upgrade_trading_member(self):
        self.get(f"/station/{self.sta}/crew/upgrade/trader")
        print("[*] Trading member upgraded.")

    def upgrade_piloting_member(self):
        self.get(f"/station/{self.sta}/crew/upgrade/pilot")
        print("[*] Piloting member upgraded.")

    def go_mine(self):
        print("[*] Starting the Mining operation")
 
        station = self.get(f"/station/{self.sta}")
        planets = self.get(f"/station/{self.sta}/scan")["planets"]
        nearest = sorted(planets,
            key=lambda pla: get_dist(station["position"], pla["position"])
        )[0]
 
        if nearest["solid"]:
            modtype = "Miner"
        else:
            modtype = "GasSucker"
 
        ship = self.get(f"/ship/{self.sid}")
        if not check_has(ship["modules"], "modtype", modtype):
            self.buy_first_mining_module(modtype, self.sta, self.sid)
        print("[*] Targeting planet at", nearest["position"])
 
        self.wait_idle(self.sid)
 
        if ship["position"] != nearest["position"]:
            self.travel(ship["id"], nearest["position"])
 
        info = self.get(f"/ship/{self.sid}/extraction/start")
        print("[*] Starting extraction:")
        for res, amnt in info.items():
            print(f"\t- Extraction of {res}: {amnt}/sec")
 
        self.wait_idle(self.sid)
        print("[*] The cargo is full, stopping mining process")
    
    def go_sell(self):
        self.wait_idle(self.sid)
        ship = self.get(f"/ship/{self.sid}")
        station = self.get(f"/station/{self.sta}")
 
        if ship["position"] != station["position"]:
            self.travel(ship["id"], station["position"])
 
        for res, amnt in ship["cargo"]["resources"].items():
            if amnt == 0.0:
                continue
            unloaded = self.get(f"/ship/{self.sid}/unload/{res}/{amnt}")
            sold = self.get(f"/market/{self.sta}/sell/{res}/{amnt}")
            print("[*] Unloaded and sold {} of {}, for {} credits".format(
                unloaded["unloaded"], res, sold["added_money"]
            ))
 
        self.ship_repair(self.sid)
        self.ship_refuel(self.sid)
    
    def buy_first_mining_module(self, modtype, sta, sid):
        all = self.get(f"/station/{sta}/shop/modules")
        mod_id = self.get(f"/station/{sta}/shop/modules/{sid}/buy/{modtype}")["id"]
 
        ship = self.get(f"/ship/{sid}")
        if not check_has(ship["crew"], "member_type", "Operator"):
            op = self.get(f"/station/{sta}/crew/hire/operator")["id"]
            self.get(f"/station/{sta}/crew/assign/{op}/{sid}/{mod_id}")

    def wait_idle(self, sid, ts=2):
        ship = self.get(f"/ship/{sid}")
        while ship["state"] != "Idle":
            time.sleep(ts)
            ship = self.get(f"/ship/{sid}")

    def travel(self, sid, pos):
        costs = self.get(f"/ship/{sid}/navigate/{pos[0]}/{pos[1]}/{pos[2]}")
        print("[*] Traveling to {}, will take {}".format(pos, costs["duration"]))
        self.wait_idle(sid, ts=costs["duration"])

    def ship_repair(self, sid):
        ship = self.get(f"/ship/{sid}")
        req = int(ship["hull_decay"])
 
        if req == 0:
            return
 
        station = self.get(f"/station/{self.sta}")["cargo"]
        if "HullPlate" not in station["resources"]:
            station["resources"]["HullPlate"] = 0
        if station["resources"]["HullPlate"] < req:
            need = req - station["resources"]["HullPlate"]
            bought = self.get(f"/market/{self.sta}/buy/hullplate/{need}")
            print(f"[*] Bought {need} of hull plates for", bought["removed_money"])
            station = self.get(f"/station/{self.sta}")["cargo"]
 
        if station["resources"]["HullPlate"] > 0:
            repair = self.get(f"/station/{self.sta}/repair/{self.sid}")
            print("[*] Repaired {} hull plates on the ship".format(repair["added-hull"]))

    def ship_refuel(self, sid):
        ship = self.get(f"/ship/{sid}")
        req = int(ship["fuel_tank_capacity"] - ship["fuel_tank"])
 
        if req == 0:
            return
 
        station = self.get(f"/station/{self.sta}")["cargo"]
        if "Fuel" not in station["resources"]:
            station["resources"]["Fuel"] = 0
        if station["resources"]["Fuel"] < req:
            need = req - station["resources"]["Fuel"]
            bought = self.get(f"/market/{self.sta}/buy/Fuel/{need}")
            print(f"[*] Bought {need} of fuel for", bought["removed_money"])
            station = self.get(f"/station/{self.sta}")["cargo"]
 
        if station["resources"]["Fuel"] > 0:
            refuel = self.get(f"/station/{self.sta}/refuel/{self.sid}")
            print("[*] Refilled {} fuel on the ship for {} credits".format(
                refuel["added-fuel"],
                bought["removed_money"],
            ))