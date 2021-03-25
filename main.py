"""
SMMO Player Checker
Author:      HugTed
Date:        03/20/2021
"""
from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image
from tkinter.scrolledtext import ScrolledText
from discord_webhook import DiscordWebhook
import webbrowser
import re
import shutil
import threading
import time
import requests
import json
import os
import sys
import configparser
import math

class MyWindow:
    def __init__(self, win):
        self.s = ttk.Style()
        self.s.theme_use('default')
        self.s.configure("blue.Horizontal.TProgressbar", foreground='cornflower blue', background='cornflower blue')
        self.s.configure('W.TButton', font = ('calibri', 10, 'bold', 'underline'), relief=SUNKEN)

        self.frame = Frame(win)
        self.frame.place(x=25, y=75)

        self.listNodes = Listbox(self.frame, width=31, height=15, font=("Helvetica", 12))
        self.listNodes.pack(side="left", fill="y")

        self.scrollbar = Scrollbar(self.frame, orient="vertical")
        self.scrollbar.config(command=self.listNodes.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.listNodes.config(yscrollcommand=self.scrollbar.set)

        self.searching = False
        self.lbl1=Label(win, text='Add ID:')
        self.t1=Entry(bd=3, width=27)
        self.btn1 = Button(win, text='Add')
        self.lbl1.place(x=25, y=25)
        self.t1.place(x=75, y=25)
        self.b1=Button(win, text='Add', command=self.addGuild)
        self.b1.place(x=260, y=23)

        self.lbl7=Label(win, text='Guilds:')
        self.lbl7.place(x=25, y=50)

        self.lbl2=Label(win, text='Options:')
        self.lbl2.place(x=375, y=25)

        self.lbl3=Label(win, text='Max Level:')
        self.lbl3.place(x=375, y=50)
        self.t2=Entry(bd=3, width=30)
        self.t2.place(x=450, y=50)

        self.lbl4=Label(win, text='Min Level:')
        self.lbl4.place(x=375, y=75)
        self.t3=Entry(bd=3, width=30)
        self.t3.place(x=450, y=75)

        self.lbl5=Label(win, text='Min Gold:')
        self.lbl5.place(x=375, y=100)
        self.t4=Entry(bd=3, width=30)
        self.t4.place(x=450, y=100)

        self.safe_mode = IntVar()
        self.is_dead = IntVar()
        self.verbose = IntVar()
        self.box1=Checkbutton(text="Remove Safe Mode", variable=self.safe_mode)
        self.box1.place(x=450, y=125)
        self.box2=Checkbutton(text="Remove Dead", variable=self.is_dead)
        self.box2.place(x=450, y=150)
        self.box2=Checkbutton(text="Verbose", variable=self.verbose)
        self.box2.place(x=450, y=175)
        self.b3=ttk.Button(win, style = 'W.TButton', text='SEARCH', width=37, command=lambda:self.start_submit_thread(None, win))
        self.b3.place(x=375, y=210)

        self.img = ImageTk.PhotoImage(Image.open(f'{dir_path}\\images\\smmo.png'))
        self.image =Label(win, image = self.img, height=140, width=140)
        self.image.place(x=440, y=245)

        self.lbl6=Label(win, text='Output:')
        self.lbl6.place(x=25, y=375)
        self.b2=Button(win, width=5, text='Clear', relief = 'groove', command=self.clearOutput)
        self.b2.place(x=75, y=372)
        self.b4=Button(win, width=5, text='Save', relief = 'groove', command=self.save)
        self.b4.place(x=118, y=372)
        self.b5=Button(win, width=5, text='Hook', relief = 'groove', state=DISABLED, command=self.sendHook)
        self.b5.place(x=161, y=372)
        self.b6=Button(win, width=5, text='Web', relief = 'groove', state=DISABLED, command=self.openWeb)
        self.b6.place(x=204, y=372)
        self.img_on = ImageTk.PhotoImage(Image.open(f'{dir_path}\\images\\on.png'))
        self.img_off = ImageTk.PhotoImage(Image.open(f'{dir_path}\\images\\off.png'))
        self.web_check = BooleanVar()
        self.web_check.set(False)
        self.b7=Button(win, borderwidth = 0, image=self.img_off, command=self.switch, relief=SUNKEN)
        self.b7.place(x=250, y=371)
        self.out1 = ScrolledText(win, height=20)
        self.out1.place(x=25, y=400)

        self.progressbar = ttk.Progressbar(win, style="blue.Horizontal.TProgressbar", length=658, mode='indeterminate')
        self.progressbar.place(x=25, y=725)

        with open(f'{dir_path}\\data\\guildlist.txt', 'r') as f:
            guildlist = json.load(f)
        for item in guildlist.values():
            self.listNodes.insert(END, item)

        if api_key == "<SMMO API KEY>":
            self.out1.insert(END, "Please make sure you have a valid SMMO API KEY in `config.ini`\n")
        if web_hook == "<DISCORD WEB HOOK>":
            self.out1.insert(END, "Please make sure you have a valid WEBHOOK in `config.ini`\n")

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
            self.out1.delete('1.0',END)
            self.out1.insert(END, "ERROR - GUILD ID ONLY")

    def switch(self):
        if self.web_check.get():
            self.b7.config(image=self.img_off)
            self.web_check.set(False)
            self.b6.config(state=DISABLED)
            self.b5.config(state=DISABLED)
        else:
            self.b7.config(image=self.img_on)
            self.web_check.set(True)
            self.b6.config(state=NORMAL)
            self.b5.config(state=NORMAL)

    def sendHook(self):
        cur_inp = self.out1.get("1.0", END)
        if len(cur_inp) >= 1900:
            index = 0
            output = "**SMMO Player Checker - Results**\n"
            search_terms = cur_inp.split("--------------")[0]
            results = cur_inp.split("--------------")[0].split("\n\n")
            output += search_terms
            while output >= 1500:
                output += results[index]
                index += 1
            output += "More..."
        else:
            output = "**SMMO Player Checker - Results**\n" + cur_inp
        webhook = DiscordWebhook(url=web_hook, content=output)
        response = webhook.execute()

    def openWeb(self):
        if self.web_check.get():
            # cur_inp = self.out1.get("1.0", END)
            # urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', cur_inp)
            # for i in range(0,len(urls)):
            #     if i == 0:
            #         webbrowser.open_new(urls[i])
            #     else:
            #         webbrowser.open_new_tab(urls[i])
            pass

    def save(self):
        cur_inp = self.out1.get("1.0", END)
        fl = open("output.txt", "w")
        fl.write(cur_inp)

    def clearOutput(self):
        self.out1.delete('1.0',END)

    def search(self):
        while self.searching == True:
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
            search_term = f'Search Params:\nMax Level: {max_level}\nMin Level: {min_level}\nMin Gold: {min_gold}\n'
            if self.safe_mode.get() == 1:
                search_term += "Safe Mode Players Removed\n"
            if self.is_dead.get() == 1:
                search_term += "Dead Players Removed\n"
            if self.verbose.get() == 1:
                search_term += "Verbose On\n"
            search_term += "--------------\n"
            self.out1.insert(END, search_term)
            self.searchUsers(users, max_level, min_level, min_gold)
            self.out1.insert(END, "Complete!\n")
            self.searching = False

    def printUser(self, lib):
        if self.verbose.get() == 0:
            self.out1.insert(END, f'[{lib["name"]}](<https://web.simple-mmo.com/user/attack/{lib["id"]}>)\n')
        else:
            self.out1.insert(END, f'Name: {lib["name"]}\nLevel: {lib["level"]}\nHP: {lib["hp"]}/{lib["max_hp"]}\nGold: {lib["gold"]}\n[Attack Link](<https://web.simple-mmo.com/user/attack/{lib["id"]}>)\n\n')

    def start_submit_thread(self, event, win):
        global submit_thread
        submit_thread = threading.Thread(target=self.search)
        self.searching = True
        submit_thread.daemon = True
        submit_thread.start()
        self.progressbar.start()
        win.after(1000, self.check_submit_thread(win))

    def check_submit_thread(self, win):
        if submit_thread.is_alive():
            win.after(1000, lambda:self.check_submit_thread(win))
        else:
            self.progressbar.stop()

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
            time.sleep(2)

sys.setrecursionlimit(5000)
dir_path = os.path.dirname(os.path.realpath(__file__))
config = configparser.ConfigParser()
config.read(f'{dir_path}\\config.ini')
api_key = config.get('DEFAULT', 'api_key')
web_hook = config.get('DEFAULT', 'web_hook')
version = config.get('DEFAULT', 'version_number')

window=Tk()
mywin=MyWindow(window)
window.title(f'SMMO Player Checker BETA v{version}')
window.iconbitmap(rf'{dir_path}\\images\\smmo.ico')
window.geometry("700x750")
window.mainloop()
