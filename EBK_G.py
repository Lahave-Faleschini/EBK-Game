import requests

API_URL = "http://127.0.0.1:8000"

#  GAME STATE 
game = {
    "p1": "",
    "p2": "",
    "scores": [0, 0],
    "turn": 0,            # 0 = p1, 1 = p2
    "step": "team",       # team -> player -> connection -> number_player -> connection ...
    "current_team": "",
    "current_player": "",
    "current_number": "",
    "consecutive_teammates": 0,
    "round_over": False
}


def current_player_name():
    return game["p1"] if game["turn"] == 0 else game["p2"]

def switch_turn():
    game["turn"] = 1 - game["turn"]

def print_instruction():
    if game["step"] == "team":
        print(f"\n{current_player_name()} — Name an NFL, NBA, or Power 5 college team")
    elif game["step"] == "player":
        print(f"\n{current_player_name()} — Name a player from {game['current_team']} who went pro")
    elif game["step"] == "connection":
        if game["consecutive_teammates"] >= 3:
            print(f"\n{current_player_name()} — Name {game['current_player']}'s jersey number or a previous team (no more teammates!)")
        else:
            print(f"\n{current_player_name()} — Name {game['current_player']}'s jersey number, previous team, or a teammate")
    elif game["step"] == "number_player":
        print(f"\n{current_player_name()} — Name a player who wore #{game['current_number']}")

#  API CALLS
def check_team(name):
    response = requests.get(f"{API_URL}/validate/team", params={"name": name})
    return response.json()

def check_player(name, team):
    response = requests.get(f"{API_URL}/validate/player", params={"name": name, "team": team})
    return response.json()

def check_jersey(player, number):
    response = requests.get(f"{API_URL}/validate/jersey", params={"player": player, "number": number})
    return response.json()

def check_teammate(player1, player2):
    response = requests.get(f"{API_URL}/validate/teammate", params={"player1": player1, "player2": player2})
    return response.json()

def check_number_player(player, number):
    response = requests.get(f"{API_URL}/validate/number_player", params={"player": player, "number": number})
    return response.json()

# ROUND HANDLING
def lose_round(reason):
    print(f"\n✗ WRONG: {reason}")
    winner = 1 - game["turn"]
    game["scores"][winner] += 1
    winner_name = game["p1"] if winner == 0 else game["p2"]
    print(f"{winner_name} wins this round!")
    print(f"Score — {game['p1']}: {game['scores'][0]}  {game['p2']}: {game['scores'][1]}")
    game["round_over"] = True

def start_new_round():
    game["step"] = "team"
    game["current_team"] = ""
    game["current_player"] = ""
    game["current_number"] = ""
    game["consecutive_teammates"] = 0
    game["round_over"] = False

def check_winner():
    if game["scores"][0] >= 5:
        print(f"\n {game['p1']} WINS THE GAME! ")
        return True
    if game["scores"][1] >= 5:
        print(f"\n {game['p2']} WINS THE GAME! ")
        return True
    return False

#  MAIN GAME LOOP 
def play():
    print("=== EBK — Prove Your Ball Knowledge ===")
    game["p1"] = input("Player 1 name: ").strip() or "Player 1"
    game["p2"] = input("Player 2 name: ").strip() or "Player 2"

    while True:
        if game["round_over"]:
            again = input("\nPress Enter to start a new round, or type 'quit' to stop: ")
            if again.lower() == "quit":
                break
            start_new_round()

        print_instruction()
        answer = input("> ").strip()
        if answer == "":
            continue

        # TEAM STEP 
        if game["step"] == "team":
            result = check_team(answer)
            if result["valid"]:
                game["current_team"] = result["team"]
                game["step"] = "player"
                switch_turn()
            else:
                lose_round(result.get("reason", "Not a valid team"))
                check_winner()
            continue

        # PLAYER STEP 
        if game["step"] == "player":
            result = check_player(answer, game["current_team"])
            if result["valid"]:
                game["current_player"] = result["player"]
                game["step"] = "connection"
                switch_turn()
            else:
                lose_round(result.get("reason", "Invalid player"))
                check_winner()
            continue

        # CONNECTION STEP (number / prev team / teammate)
        if game["step"] == "connection":
            # Try jersey number first
            if answer.isdigit():
                result = check_jersey(game["current_player"], int(answer))
                if result["valid"]:
                    game["current_number"] = answer
                    game["step"] = "number_player"
                    game["consecutive_teammates"] = 0
                    switch_turn()
                else:
                    lose_round(result.get("reason", "Invalid jersey number"))
                    check_winner()
                continue

            # Try as a teammate
            if game["consecutive_teammates"] < 3:
                result = check_teammate(game["current_player"], answer)
                if result["valid"]:
                    game["current_player"] = answer
                    game["consecutive_teammates"] += 1
                    switch_turn()
                    continue

            # Try as a previous team
            result = check_team(answer)
            if result["valid"]:
                # Confirm the current player actually played there
                player_check = check_player(game["current_player"], answer)
                if player_check["valid"]:
                    game["current_team"] = result["team"]
                    game["step"] = "player"
                    game["consecutive_teammates"] = 0
                    switch_turn()
                    continue

            lose_round(f"'{answer}' is not a valid jersey number, teammate, or previous team")
            check_winner()
            continue

        #  NUMBER_PLAYER STEP 
        if game["step"] == "number_player":
            result = check_number_player(answer, int(game["current_number"]))
            if result["valid"]:
                game["current_player"] = result["player"]
                game["step"] = "connection"
                game["consecutive_teammates"] = 0
                switch_turn()
            else:
                lose_round(result.get("reason", "Invalid player for that number"))
                check_winner()
            continue

if __name__ == "__main__":
    play()