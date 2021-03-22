"""
SMMO Player Checker
Author:      HugTed
Date:        03/20/2021
"""
from tkinter import *
from tkinter.scrolledtext import ScrolledText
import time
import requests
import json
import os
import configparser

class MyWindow:
    def __init__(self, win):
        self.lbl1=Label(win, text='Add ID:')
        self.t1=Entry(bd=3)
        self.btn1 = Button(win, text='Add')
        self.lbl1.place(x=25, y=25)
        self.t1.place(x=75, y=25)
        self.b1=Button(win, text='Add', command=self.addGuild)
        self.b1.place(x=225, y=23)

        self.lbl7=Label(win, text='Guilds:')
        self.lbl7.place(x=25, y=50)

        self.lbl2=Label(win, text='Options:')
        self.lbl2.place(x=300, y=25)

        self.lbl3=Label(win, text='Max Level:')
        self.lbl3.place(x=300, y=50)
        self.t2=Entry(bd=3)
        self.t2.place(x=375, y=50)

        self.lbl4=Label(win, text='Min Level:')
        self.lbl4.place(x=300, y=75)
        self.t3=Entry(bd=3)
        self.t3.place(x=375, y=75)

        self.lbl5=Label(win, text='Min Gold:')
        self.lbl5.place(x=300, y=100)
        self.t4=Entry(bd=3)
        self.t4.place(x=375, y=100)

        self.safe_mode = IntVar()
        self.is_dead = IntVar()
        self.verbose = IntVar()
        self.box1=Checkbutton(text="Remove Safe Mode", variable=self.safe_mode)
        self.box1.place(x=375, y=125)
        self.box2=Checkbutton(text="Remove Dead", variable=self.is_dead)
        self.box2.place(x=375, y=150)
        self.box2=Checkbutton(text="Verbose", variable=self.verbose)
        self.box2.place(x=375, y=175)

        self.lbl6=Label(win, text='Output:')
        self.lbl6.place(x=25, y=475)
        self.b2=Button(win, text='Clear', command=self.clearOutput)
        self.b2.place(x=75, y=473)
        self.out1 = ScrolledText(win)
        self.out1.place(x=25, y=500)

        self.b3=Button(win, text='Search', command=self.search)
        self.b3.place(x=300, y=200)

        self.frame = Frame(win)
        self.frame.place(x=25, y=75)

        self.listNodes = Listbox(self.frame, width=25, height=20, font=("Helvetica", 12))
        self.listNodes.pack(side="left", fill="y")

        self.scrollbar = Scrollbar(self.frame, orient="vertical")
        self.scrollbar.config(command=self.listNodes.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.listNodes.config(yscrollcommand=self.scrollbar.set)

        with open(f'{dir_path}\\data\\guildlist.txt', 'r') as f:
            guildlist = json.load(f)
        for item in guildlist.values():
            self.listNodes.insert(END, item)

        if api_key == "<SMMO API KEY>":
            self.out1.insert(END, "Please make sure you have a valid SMMO API KEY in `config.ini`\n")

    def addGuild(self):
        id = str(self.t1.get())
        with open(f'{dir_path}\\data\\guildlist.txt', 'r') as f:
            guildlist = json.load(f)
        endpoint = f'https://api.simple-mmo.com/v1/guilds/info/{id}'
        payload = {'api_key': api_key}
        try:
            r = requests.post(url = endpoint, data = payload)
            lib = r.json()
            guildlist[f'{id}'] = lib["name"]
            with open(f'{dir_path}\\data\\guildlist.txt', 'w') as f:
                json.dump(guildlist, f)
            self.listNodes.insert(END, lib["name"])
        except:
            self.t1.delete(0,END)
            self.t1.insert(END, "ERROR - GUILD ID ONLY")

    def clearOutput(self):
        self.out1.delete('1.0',END)

    def search(self):
        guild_name=str((self.listNodes.get(ACTIVE)))
        guild_id = 0
        self.out1.delete('1.0',END)
        if guild_name == "":
            self.out1.insert(END, "ERROR")
            return
        with open(f'{dir_path}\\data\\guildlist.txt', 'r') as f:
            guildlist = json.load(f)
        for id, name in guildlist.items():
            if name == guild_name:
                guild_id = id
        if guild_id == 0:
            self.out1.insert(END, "ERROR")
            return
        self.out1.insert(END, f'Found Guild - {guild_id}\n')
        users = []
        endpoint = f'https://api.simple-mmo.com/v1/guilds/members/{guild_id}'
        payload = {'api_key': api_key}
        r = requests.post(url = endpoint, data = payload)
        lib = r.json()
        for user in lib:
            users.append(user["user_id"])
        with open(f'{dir_path}\\data\\{guild_id}.txt', 'w') as f:
            json.dump(users, f)
        self.out1.insert(END, f'Found Members - {len(users)}\n')
        try:
            max_level = int(self.t2.get())
        except:
            max_level = 1000000
        try:
            min_level = int(self.t3.get())
        except:
            min_level = 0
        try:
            min_gold = int(self.t4.get())
        except:
            min_gold = 0
        self.out1.insert(END, f'Search Params:\nMax Level: {max_level}\nMin Level: {min_level}\nMin Gold: {min_gold}\n--------------\n')
        self.searchUsers(users, max_level, min_level, min_gold)
        self.out1.insert(END, "Complete!\n")

    def printUser(self, lib):
        if self.verbose.get() == 0:
            self.out1.insert(END, f'{lib["name"]} - https://web.simple-mmo.com/user/attack/{lib["id"]}\n')
        else:
            self.out1.insert(END, f'Name: {lib["name"]}\nLevel: {lib["level"]}\nHP: {lib["hp"]}/{lib["max_hp"]}\nGold: {lib["gold"]}\nhttps://web.simple-mmo.com/user/attack/{lib["id"]}\n\n')

    def searchUsers(self, users, max_level, min_level, min_gold):
        index = 0
        error_index = 0
        for userid in users:
            try:
                endpoint = "https://api.simple-mmo.com/v1/player/info/" + f'{userid}'
                payload = {'api_key': api_key}
                r = requests.post(url = endpoint, data = payload)
                lib = r.json()
                index += 1
                if lib["level"] >= min_level and lib["level"] <= max_level and lib["gold"] >= min_gold:
                    if self.safe_mode.get() == 1 and self.is_dead.get() == 1:
                        if lib["safeMode"] == 0 and int(lib["hp"]*2) > lib["max_hp"]:
                            self.printUser(lib)
                    elif self.is_dead.get() == 1:
                        if int(lib["hp"]*2) > lib["max_hp"]:
                            self.printUser(lib)
                    elif self.safe_mode.get() == 1:
                        if lib["safeMode"] == 0:
                            self.printUser(lib)
                    else:
                        self.printUser(lib)

            except Exception as e:
                print(e)
                error_index += 1
                if error_index == 10:
                    self.out1.insert(END, f'You might be rate limited, please try again later!')
            time.sleep(1)

dir_path = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(f'{dir_path}\\config.ini')
api_key = config.get('DEFAULT', 'api_key')

window=Tk()
mywin=MyWindow(window)
window.title('SMMO Player Checker BETA v0.2')
window.geometry("700x900")
window.mainloop()
