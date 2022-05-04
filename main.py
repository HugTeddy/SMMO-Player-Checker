"""
SMMO Player Checker
Author:      HugTed
Date:        05/3/2022
Version:     0.11.1
"""
import configparser
import json
import random
import threading
import time
import webbrowser
from datetime import datetime, timedelta
import PySimpleGUI as sg
import keyboard
import requests
from websocket import create_connection


# LOAD CONFIG
config = configparser.ConfigParser()
config.read(f'./config.ini')
API_KEY = config.get('DEFAULT', 'API_KEY')
WEB_HOOK = config.get('DEFAULT', 'web_hook')
OWN_GUILD = int(config.get('DEFAULT', 'own_guild'))
KEY1 = config.get('DEFAULT', 'hotkey1')
KEY2 = config.get('DEFAULT', 'hotkey2')
VERSION = config.get('DEFAULT', 'version_number')
THEME = config.get('DEFAULT', 'theme')
with open("./data/banned.txt", "r") as f:
    BANNED_LIST = json.load(f)
with open("./data/temp.txt", "r") as f:
    TEMP_LIST = json.load(f)
with open(f'./data/guildlist.txt', 'r') as f:
    GUILD_LIST = json.load(f)
DEFAULT_LIST = ["Guild Wars", "All Players"]
for guilds in GUILD_LIST.values():
    DEFAULT_LIST.append(guilds)
TARGET_INDEX = 0
WAR_LIST = []
TARGET_LIST = []
TARGET_DATA = []
SEARCHING = False


# GUI SETUP
if THEME.lower() == "dark":
    sg.theme('Dark Grey 12')
else:
    sg.theme('Default1')
FONT = 'TkFixedFont'

layoutA = [
    [sg.Text('Guild ID:', font=FONT), sg.InputText(font=FONT), sg.Button(button_text="Add", font=FONT)],
    [sg.Listbox(DEFAULT_LIST, default_values=["Guild Wars"],
                select_mode="multiple", expand_x=True, size=(20, 10), font=FONT, k="Guild List")],
    [sg.Button(button_text="Stop", font=FONT), sg.Button(button_text="Clear", font=FONT),
     sg.Button(button_text="Clear List", font=FONT), sg.Button(button_text="Client", font=FONT)]
]

layoutB = [
    [sg.Text('Options', font=FONT)],
    [sg.Text('Max Level:'.ljust(10), font=FONT), sg.InputText(size=(20, 1), font=FONT)],
    [sg.Text('Min Level:'.ljust(10), font=FONT), sg.InputText(size=(20, 1), font=FONT)],
    [sg.Text('Gold:'.ljust(10), font=FONT), sg.InputText(size=(20, 1), font=FONT)],
    [sg.Checkbox("Remove Safe Mode", font=FONT)],
    [sg.Checkbox("Remove Dead", font=FONT)],
    [sg.Button(button_text="Search", font=FONT, expand_x=True)],
    [sg.InputText(size=(20, 1), font=FONT), sg.Button(button_text="Temp", font=FONT),
     sg.Button(button_text="Ban", font=FONT)],
]

mainlayout = [
    [sg.Column(layoutA), sg.Column(layoutB)],
    [sg.Table(values=[], headings=["ID", "Name", "Level", "Gold", "Banned", "Kills"], auto_size_columns=True, k="tree",
              font=FONT, expand_x=True, num_rows=12, justification="center")],
    [sg.Multiline("", font=FONT, expand_x=True, size=(0, 5), k="Output")]
]


# Functions
# Setup Params + Choosing Search Options
def startSearch(window, value):
    global WAR_LIST, SEARCHING

    if SEARCHING == True:
        window["Output"].print('Search is in progress, please stop current search first.')
        return

    param = {}
    if value[1] != "" and value[1].isdigit():
        param["max_level"] = int(value[1])
    else:
        param["max_level"] = 10000000

    if value[2] != "" and value[2].isdigit():
        param["min_level"] = int(value[2])
    else:
        param["min_level"] = 0

    if value[3] != "" and value[3].isdigit():
        param["gold"] = int(value[3])
    else:
        param["gold"] = 0

    if value[4]:
        param["safeMode"] = True

    if value[5]:
        param["dead"] = True

    if len(values['Guild List']) == 1 and values['Guild List'][0] == "Guild Wars":
        callWarInfo()
        if len(WAR_LIST) == 0:
            window["Output"].print("ERROR: Unable to find war guilds, you may be on hold.")
            return
        if param["gold"] != 0:
            window["Output"].print("WARNING: Gold Search Not Available Through Wars")
        SEARCHING = True
        window["Output"].print('**Starting War Search**')
        threading.Thread(target=searchWar, args=(window, param), daemon=True).start()
    elif len(values['Guild List']) == 1 and values['Guild List'][0] == "All Players":
        users = random.sample(range(100, 700000), 25000)
        SEARCHING = True
        window["Output"].print('**Starting All Players Search**')
        threading.Thread(target=searchPlayer, args=(window, users, param), daemon=True).start()
    elif "All Players" not in values['Guild List'] and "Guild Wars" not in values['Guild List']:
        guilds = []
        for guildname in values['Guild List']:
            guildID = getGuildID(guildname)
            if guildID != -1:
                guilds.append(guildID)
        SEARCHING = True
        window["Output"].print('**Starting Guild Search**')
        threading.Thread(target=searchGuild, args=(window, guilds, param), daemon=True).start()
    else:
        window["Output"].print('Error with Guild Selection')


# Search Function - Wars
def searchWar(window, param):
    global WAR_LIST, API_KEY, TARGET_LIST, TARGET_DATA, SEARCHING
    kill_timestamp = (datetime.now() - timedelta(hours=48)).timestamp()
    for guild in WAR_LIST:
        if not SEARCHING:
            window["Output"].print(f'Halting Search')
            return
        try:
            endpoint = f"https://api.simple-mmo.com/v1/guilds/members/{guild}"
            payload = {'api_key': API_KEY}
            r = requests.post(url=endpoint, data=payload)
            lib = r.json()
            if r.status_code != 200:
                window["Output"].print(f'API Error, please check your key and try again later!')
                time.sleep(2)
                continue
        except:
            window["Output"].print(f'Error Locating Guild: {guild}')
            time.sleep(2)
            continue
        for user in lib:
            if user["safe_mode"] == 0 and user["current_hp"] * 2 >= user["max_hp"]:
                if user["level"] > 200 or (user["last_activity"] < kill_timestamp and user["level"] <= 200):
                    if param["min_level"] <= user["level"] <= param["max_level"]:
                        TARGET_LIST.append(user["user_id"])
                        TARGET_DATA.append(user)
        window["Output"].print(f'Searching Guild: {guild}')
        updateTable(window)
        time.sleep(2)
    window["Output"].print(f'Search Complete')
    SEARCHING = False
    window.write_event_value('--Complete--', '')


# Search Function - Guild
def searchGuild(window, guilds, param):
    global API_KEY, TARGET_LIST, TARGET_DATA, SEARCHING
    for guild in guilds:
        if not SEARCHING:
            window["Output"].print(f'Halting Search')
            return
        try:
            endpoint = f"https://api.simple-mmo.com/v1/guilds/members/{guild}"
            payload = {'api_key': API_KEY}
            r = requests.post(url=endpoint, data=payload)
            libs = r.json()
            if r.status_code != 200:
                window["Output"].print(f'API Error, please check your key and try again later!')
                time.sleep(2)
                continue
        except:
            window["Output"].print(f'API Error, please check your key and try again later!')
            time.sleep(2)
            continue
        for lib in libs:
            if param["min_level"] <= lib["level"] <= param["max_level"]:
                if "safeMode" in param.keys() and "dead" in param.keys():
                    if lib["safe_mode"] == 0 and int(lib["current_hp"] * 2) > lib["max_hp"]:
                        TARGET_DATA.append(lib)
                        TARGET_LIST.append(lib["user_id"])
                elif "safeMode" in param.keys():
                    if lib["safe_mode"] == 0:
                        TARGET_DATA.append(lib)
                        TARGET_LIST.append(lib["user_id"])
                elif "dead" in param.keys():
                    if int(lib["current_hp"] * 2) > lib["max_hp"]:
                        TARGET_DATA.append(lib)
                        TARGET_LIST.append(lib["user_id"])
                else:
                    TARGET_DATA.append(lib)
                    TARGET_LIST.append(lib["user_id"])
        window["Output"].print(f'Searching Guild: {guild}')
        updateTable(window)
        time.sleep(2)
    window["Output"].print(f'Search Complete')
    SEARCHING = False
    window.write_event_value('--Complete--', '')


# Search Function - Players
def searchPlayer(window, users, param):
    global API_KEY, TARGET_LIST, TARGET_DATA, SEARCHING
    for user in users:
        if not SEARCHING:
            window["Output"].print(f'Halting Search')
            return
        try:
            endpoint = f"https://api.simple-mmo.com/v1/player/info/{user}"
            payload = {'api_key': API_KEY}
            r = requests.post(url=endpoint, data=payload)
            lib = r.json()
            if "error" in lib.keys():
                time.sleep(2)
                continue
            if r.status_code != 200:
                window["Output"].print(f'API Error, please check your key and try again later!')
                time.sleep(2)
                continue
        except:
            window["Output"].print(f'API Error, please check your key and try again later!')
            time.sleep(2)
            continue
        lib["user_id"] = lib["id"]
        if param["min_level"] <= lib["level"] <= param["max_level"] and lib["gold"] > param["gold"]:
            if "safeMode" in param.keys() and "dead" in param.keys():
                if lib["safeMode"] == 0 and int(lib["hp"] * 2) > lib["max_hp"]:
                    TARGET_DATA.append(lib)
                    TARGET_LIST.append(lib["id"])
            elif "safeMode" in param.keys():
                if lib["safeMode"] == 0:
                    TARGET_DATA.append(lib)
                    TARGET_LIST.append(lib["id"])
            elif "dead" in param.keys():
                if int(lib["hp"] * 2) > lib["max_hp"]:
                    TARGET_DATA.append(lib)
                    TARGET_LIST.append(lib["id"])
            else:
                TARGET_DATA.append(lib)
                TARGET_LIST.append(lib["id"])
        window["Output"].print(f'Searching User: {user}')
        updateTable(window)
        time.sleep(2)
    window["Output"].print(f'Search Complete')
    SEARCHING = False
    window.write_event_value('--Complete--', '')


# open client
def openYomu(data):
    try:
        ws = create_connection("ws://localhost:8069")
        msg = {"type": "openLink", "url": f"https://simple-mmo.com/user/attack/{data}?new_page=true"}
        ws.send(json.dumps(msg, separators=(',', ':')))
        result = ws.recv()
        ws.close()
        if result == "success":
            return True
        else:
            return False
    except:
        webbrowser.open(f'https://web.simple-mmo.com/user/attack/{data}?new_page=true', autoraise=True)
        return False


# API Call: Guild Info
def callGuildInfo(id):
    global GUILD_LIST, API_KEY
    endpoint = f'https://api.simple-mmo.com/v1/guilds/info/{id}'
    payload = {'api_key': API_KEY}
    try:
        r = requests.post(url=endpoint, data=payload)
        lib = r.json()
        GUILD_LIST[f'{id}'] = lib["name"]
        with open(f'./data/guildlist.txt', 'w') as f:
            json.dump(GUILD_LIST, f)
        return lib
    except:
        return -1


# API Call: Guild Members
def callGuildMember(id):
    global API_KEY
    try:
        endpoint = f"https://api.simple-mmo.com/v1/guilds/members/{id}"
        payload = {'api_key': API_KEY}
        r = requests.post(url=endpoint, data=payload)
        lib = r.json()
        if r.status_code != 200:
            return -1
        else:
            return lib
    except:
        return -1


# API Call: Player Info
def callPlayer(id):
    global API_KEY
    try:
        endpoint = "https://api.simple-mmo.com/v1/player/info/" + f'{id}'
        payload = {'api_key': API_KEY}
        r = requests.post(url=endpoint, data=payload)
        lib = r.json()
        if "error" not in lib.keys():
            return -1
        elif r.status_code != 200:
            return -1
        else:
            return lib
    except:
        return -1


# API Call: War Info
def callWarInfo():
    global WAR_LIST, OWN_GUILD, API_KEY
    endpoint = f'https://api.simple-mmo.com/v1/guilds/wars/{OWN_GUILD}/1'
    payload = {'api_key': API_KEY}
    r = requests.post(url=endpoint, data=payload)
    lib = r.json()
    for war in lib:
        if war["guild_1"]["id"] != OWN_GUILD:
            WAR_LIST.append(war["guild_1"]["id"])
        else:
            WAR_LIST.append(war["guild_2"]["id"])
    return 1


# Get Next Player
def newPlayer():
    global TARGET_LIST, TARGET_INDEX, TEMP_LIST, BANNED_LIST
    while len(TARGET_LIST)-1 > TARGET_INDEX:
        if TEMP_LIST.count(TARGET_LIST[TARGET_INDEX]) == 3:
            TARGET_INDEX += 1
        elif TARGET_LIST[TARGET_INDEX] in BANNED_LIST:
            TARGET_INDEX += 1
        else:
            break

    if len(TARGET_LIST) <= TARGET_INDEX + 1:
        return False

    res = openYomu(TARGET_LIST[TARGET_INDEX])
    TEMP_LIST.append(TARGET_LIST[TARGET_INDEX])
    TARGET_INDEX += 1

    if TARGET_INDEX % 10 == 0:
        with open("./data/temp.txt", "w") as f:
            json.dump(TEMP_LIST, f)

    return res


# Ban/Unban Player
def banPlayer(playerid=None):
    global TARGET_LIST, TARGET_INDEX, BANNED_LIST
    if playerid == None:
        if TARGET_LIST[TARGET_INDEX] in BANNED_LIST:
            BANNED_LIST.remove(TARGET_LIST[TARGET_INDEX])
        else:
            BANNED_LIST.append(TARGET_LIST[TARGET_INDEX])
        with open("./data/banned.txt", "w") as f:
            json.dump(BANNED_LIST, f)
    else:
        if int(playerid) in BANNED_LIST:
            BANNED_LIST.remove(int(playerid))
        else:
            BANNED_LIST.append(int(playerid))
        with open("./data/banned.txt", "w") as f:
            json.dump(BANNED_LIST, f)
    TARGET_INDEX += 1
    newPlayer()


# Check Ban List
def checkBan(user):
    global BANNED_LIST
    if int(user) in BANNED_LIST:
        return "X"
    else:
        return "O"


# Remove Player from Kill List
def clearTemp(playerid=None):
    global TEMP_LIST
    if playerid == None:
        TEMP_LIST = []
    else:
        TEMP_LIST[:] = [x for x in TEMP_LIST if x != playerid]
    with open("./data/temp.txt", "w") as f:
        json.dump(TEMP_LIST, f)


# Check Player Kills
def checkTemp(user):
    global TEMP_LIST
    return TEMP_LIST.count(int(user))


# Update Table of Players
def updateTable(window):
    global TARGET_DATA, TARGET_INDEX
    if len(TARGET_DATA) != 0:
        output_list = []
        for user in TARGET_DATA:
            if "gold" in user.keys():
                output_list.append(
                    [user["user_id"], user["name"], f'{user["level"]:,}', f'{user["gold"]:,}', checkBan(user["user_id"]), checkTemp(user["user_id"])])
            else:
                output_list.append(
                    [user["user_id"], user["name"], f'{user["level"]:,}', f'N/A', checkBan(user["user_id"]), checkTemp(user["user_id"])])
        window["tree"].Update(values=output_list, select_rows=[TARGET_INDEX])
        window["tree"].set_vscroll_position(TARGET_INDEX / len(TARGET_DATA))
    else:
        window["tree"].Update(values=[])


# Get Guild ID from Name
def getGuildID(val):
    global GUILD_LIST
    for key, value in GUILD_LIST.items():
        if val == value:
            return int(key)
    return -1


if __name__ == "__main__":
    window = sg.Window(f'SimpleMMO Player Checker v{VERSION}', mainlayout, icon=r'./images/smmo.ico')

    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, 'Cancel'):
            break
        elif event == "Add":
            if values[0] != '':
                data = callGuildInfo(values[0])
                print(data)
                output = ["Guild Wars", "All Players"]
                for items in GUILD_LIST.values():
                    output.append(items)
                window["Guild List"].update(output)
        elif event == "Search" and SEARCHING == False:
            startSearch(window, values)
        elif event == "Stop":
            SEARCHING = False
        elif event == "Client":
            keyboard.add_hotkey(KEY1, lambda: window.write_event_value('--NewPlayerY--', ''))
            keyboard.add_hotkey(KEY2, lambda: window.write_event_value('--BanPlayerY--', ''))
            if len(TARGET_LIST) == 0:
                window["Output"].print("Empty Target List, Please Search First")
            elif not openYomu(TARGET_LIST[0]):
                window["Output"].print("Unable to open Y0mu's Client, Defaulting to Web App.")
        elif event == "--NewPlayerY--":
            newPlayer()
        elif event == "--BanPlayerY--":
            banPlayer()
        elif event == "Ban":
            if values[6] != "" and values[6].isdigit():
                banPlayer(int(values[6]))
        elif event == "Temp":
            if values[6] != "" and values[6].isdigit():
                clearTemp(int(values[6]))
        elif event == "Clear":
            TARGET_LIST = []
            TARGET_DATA = []
            updateTable(window)
        elif event == "Clear List":
            clearTemp()

        updateTable(window)
    window.close()
