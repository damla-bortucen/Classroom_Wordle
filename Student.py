import string
import random
import struct
import socket
import sys
import os
import json

from PyDictionary import PyDictionary
from kivy.app import App
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.stacklayout import StackLayout
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.button import Button


def resource_path(dictionary_file):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, dictionary_file)

# valid words for random selection that has a meaning in wldict database
dictpath = resource_path("wordlist.json")
with open (dictpath, "r") as f:
    wldict = json.load(f)
    mainwordlist = wldict.keys()

# all words that user can enter including the ones that does not have a meaning in database
dictpath = resource_path("bigdict.txt")
with open (dictpath, "r") as f:
    bigdict = [i[:-1].upper() for i in f.readlines()]
 



class MyWordle(App):
    pass

cell_full = [0.4, 0.9, 0.8, 1]  # R,G,B,A
cell_empty = [1, 1, 1, 1]
green = [0, 1, 0, 1]
yellow = [1, 1, 0, 1]

won = False
number_of_letters = 5
number_of_tries = number_of_letters + 1
game_started = False
target_word = None
myp = None
svgame = False

class WindowManager(ScreenManager):
    pass

class StartScreen(Screen):
    def startcallback(self):
        global target_word
        target_word = None
        # delete the contents of message box widget used in start screen
        self.children[0].children[4].text = ""



class MyPopup(Popup):
    def on_enter(self, val):
        if self.uname.text:
            self.closepopup()
    uname = TextInput(multiline=False, halign="center")
    
    def __init__(self, gms, wdw, s, **kwargs):
        super().__init__(**kwargs)
        self.gamesc = gms
        self.windw = wdw
        self.sock = s
        popupboxlayout = BoxLayout(orientation="vertical", spacing=dp(120), padding=(dp(10), dp(10)))
        self.uname.bind(on_text_validate=self.on_enter)
        popupboxlayout.add_widget(self.uname)
        popupboxlayout.children[0].font_size = self.height/2
        popupboxlayout.children[0].focus = True
        closeButton = Button(text="Start Game")
        closeButton.bind(on_release=self.closepopup)
        popupboxlayout.add_widget(closeButton)
        self.add_widget(popupboxlayout)

    def closepopup(self, *args):
        if self.uname.text:
            message = 'username' + self.uname.text
            multicast_group = ('224.5.55.25', 15555)
            sent = self.sock.sendto(message.encode(), multicast_group)
            self.dismiss()
            self.gamesc.InitializeDictionaryAndGame(self.windw)
            
            


class GameScreen(Screen):
  
 
    
    def StartNewGame(self, gamelevel, servergame, wdw, msgbox):

        global target_word
        global number_of_letters
        global number_of_tries
        global filtered_list
        global charset
        global won
        global myp
        global s
        global multicast_group
        global svgame
                       
        #won = False
        svgame = servergame
        filtered_list = []
        #charset = {x:0 for x in list(string.ascii_uppercase)}

        if not servergame:
            # build the list of words according to user selection
            number_of_letters = gamelevel
            number_of_tries = gamelevel + 1
            
            i=0
            for i in mainwordlist:
                if len(i) == gamelevel:
                    filtered_list.append(i)

            target_word = random.choice(filtered_list)
            #for test purposes
            #print(target_word)
            self.InitializeDictionaryAndGame(wdw)
           
        else:
            message = 'Get Word'
            multicast_group = ('224.5.55.25', 15555)
            
            # Create UDP socket object
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)     
    
            # Set a timeout so the socket does not block indefinitely when
            # trying to receive data.
            s.settimeout(0.5)     
            # Set the time-to-live for messages to 1 so they do not go. 
            # past the local network segment. pack it into 1 byte
            ttl = struct.pack('b', 1)
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)


            # Send data to the multicast group
            sent = s.sendto(message.encode(), multicast_group)
            # Look for responses from all recipients
            try:
                data, server = s.recvfrom(16)
            except socket.timeout:
                msgbox.text = 'No Game Available'
                print('closing socket')
                s.close()
            else:
                target_word = data.decode().upper()
                msgbox.text = ""

                # test purposes
                # print('received "%s" from %s' % (target_word, server))
                
                i=0
                number_of_letters = len(target_word)
                number_of_tries = len(target_word) + 1
                """for i in mainwordlist:
                    if len(i) == number_of_letters:
                        filtered_list.append(i)"""

                if not myp:
                    myp = MyPopup(self, wdw, s, auto_dismiss=False,size_hint=(0.5,0.5),title="Enter Username")
                else:
                    myp.children[0].children[0].children[0].children[1].focus = True
                myp.open()
            
                """else:
                    message = 'username' + myp.uname.text
                    multicast_group = ('224.5.55.25', 15555)
                    sent = myp.sock.sendto(message.encode(), multicast_group)
                    self.InitializeDictionaryAndGame(wdw)
                """

    def InitializeDictionaryAndGame(self, wdw):

        global target_word
        global number_of_letters
        global number_of_tries
        global game_started
        global filtered_list
        global meaning_message
        global charset
        global won

        won = False
        charset = {x:0 for x in list(string.ascii_uppercase)}
        filtered_list = []
        if target_word:
            i=0
            number_of_letters = len(target_word)
            number_of_tries = len(target_word) + 1
            for i in mainwordlist:
                if len(i) == number_of_letters:
                    filtered_list.append(i)

            # extract the meaning from dictionary and store in the meaning_message global variable
            meaning_message = target_word + ':\n\n' + wldict[target_word]
              
            # Delete all lines in inputform except the check button.
            wdw.current = "Game"
            wdw.transition.direction = "left"
            if game_started:
                self.children[0].children[1].clear_widgets([x for x in self.children[0].children[1].children if self.children[0].children[1].children.index(x) < (len(self.children[0].children[1].children)-1)])

            # Initialize the inputform, letter form, and populate the letter form
            # self is gamescreen, children[0] is wordle rootform, children [1] is input form
            self.children[0].children[1].children[0].disabled = False
            self.children[0].children[1].InitializeInputForm()
            self.children[0].children[0].children[3].InitializeRMLForm()
            self.children[0].children[0].children[3].updateletters()
            self.children[0].user_message = ''
            self.children[0].meaning_message = ""

            game_started = True


class ServerSwitch(Switch):
    def __init__(self, **kwargs):
        self.bind(active=self.switch_changed)
        super().__init__(**kwargs)

    def switch_changed(self, instance, value):
        print(instance)
        if value:
            instance.parent.parent.children[1].disabled = True
            instance.parent.parent.children[2].disabled = True
        else: 
            instance.parent.parent.children[1].disabled = False
            instance.parent.parent.children[2].disabled = False
       


class WordleRootForm(BoxLayout):
    checkbutton = ObjectProperty(None)
    rml = ObjectProperty(None)
    user_message = StringProperty("")
    meaning_message = StringProperty("")

    def __init__(self, **kwargs):
        Window.bind(on_key_down=self.On_Keyboard_Down)
        super().__init__(**kwargs)

    def On_Keyboard_Down(self, instance, scancode, keycode, text, modifiers):
        global game_started
        if game_started:
            allboxesfull = True
            for i in range(number_of_letters):
                if not self.children[1].children[self.children[1].currentline].children[i].text:
                    allboxesfull = False
                    break
            if keycode == 40 and allboxesfull:  # 40 - Enter key pressed
                self.checkbutton.parent.on_check_click(self.rml, self.checkbutton)



class OneLetterInput(TextInput):

    def on_text_validate(self):
        if self.text and not won:
            self.background_color = cell_empty
            self.cursor_color = cell_empty


    def insert_text(self, substring, from_undo=False):
        s = substring.upper()
        if s.isalpha():
            if len(self.text) == 1:
                self.text = ''
            if self.focus_next == StopIteration:
                self.background_color = cell_full
                self.cursor_color = cell_full
            else:
                nextitem = self.get_focus_next()
                self.background_color = cell_full
                self.cursor_color = cell_full
                nextitem.focus = True
                nextitem.background_color = cell_empty
                nextitem.cursor_color = cell_empty
        else:
            s = ""

        return super().insert_text(s, from_undo=from_undo)

    def do_backspace(self, from_undo=False, mode="bkspc"):
        if len(self.text) > 0:
            self.background_color = cell_empty
            self.cursor_color = cell_empty
            self.text = ''
        elif self.focus_previous != StopIteration:
            nextitem = self.get_focus_previous()
            if self.text:
                self.background_color = cell_full
                self.cursor_color = cell_full
            else:
                self.background_color = cell_empty
                self.cursor_color = cell_empty
            nextitem.focus = True
            if len(nextitem.text) > 0:
                nextitem.text = ""
                nextitem.background_color = cell_empty
                nextitem.cursor_color = cell_empty
        return True

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            for widget in self.parent.children:
                if widget.text == "":
                    widget.background_color = cell_empty
                    widget.cursor_color = cell_empty
                else:
                    widget.background_color = cell_full
                    widget.cursor_color = cell_full
            self.background_color = cell_empty
            self.cursor_color = cell_empty
        return super().on_touch_down(touch)


class OneLineInput(BoxLayout):
    # divide the remaining layout between tries after the check word button
    boxheight = (1 - 0.15) / number_of_tries

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for i in range(number_of_letters):
            charbox = OneLetterInput(background_color=cell_empty)
            if i == 0:
                charbox.focus_previous = StopIteration
            elif i == (number_of_letters - 1):
                charbox.focus_next = StopIteration
            self.add_widget(charbox)

    def add_line_number(self, line_number):
        self.add_widget(Label(text="[b]" + str(line_number) + "[/b]", size_hint_x=0.3, color=[1, 0, 0, 1], markup=True,
                              halign="right"), index=number_of_letters)


class InputForm(BoxLayout):

    def InitializeInputForm(self):
        for i in range(number_of_tries):
            newline = OneLineInput()
            newline.add_line_number(i + 1)
            if i != 0:
                newline.disabled = True
            self.add_widget(newline)
            self.currentline = number_of_tries - 1
        self.children[number_of_tries-1].children[number_of_letters - 1].focus = True


    def on_check_click(self, rml, chkbtn):
        # find the entered word combining letters in the row
        entered_word = ""
        global won

        # read letters and construct word
        for i in range(number_of_letters - 1, -1, -1):
            entered_word += self.children[self.currentline].children[i].text

        # make all background fullcolor as user might have pressed check when focus was not on last letter
        if len(entered_word) == number_of_letters:
            for i in range(number_of_letters - 1, -1, -1):
                self.children[self.currentline].children[i].cursor_color = cell_full
                self.children[self.currentline].children[i].background_color = cell_full


            if entered_word not in bigdict:
                self.parent.user_message = "Invalid word! Try again"

                self.children[self.currentline].children[number_of_letters - 1].focus = True
                self.children[self.currentline].children[number_of_letters - 1].background_color = cell_empty
                self.children[self.currentline].children[number_of_letters - 1].cursor_color = cell_empty


            # valid word
            else:
                self.parent.user_message = ""
                if entered_word == target_word:
                    won = True

                for i in range(len(entered_word)):
                    charset[entered_word[i]] = 1
                    if (entered_word[i] == target_word [i]):
                        charset[entered_word[i]] = 3
                        self.children[self.currentline].children[number_of_letters-1-i].background_color = green

                    for i2 in range(len(target_word)):
                        if (entered_word[i] == target_word[i2]) and (i != i2) and (entered_word[i] != target_word[i]):
                            if charset[entered_word[i]] != 3:
                                charset[entered_word[i]] = 2
                            self.children[self.currentline].children[number_of_letters-1-i].background_color = yellow

                #update remaining letters with the used letters
                rml.updateletters()

                if won:
                    self.parent.user_message = "Correct! You win!"
                    self.parent.meaning_message = meaning_message
                    if svgame and not chkbtn.disabled:
                        message =  "result" + "S" + myp.uname.text + " " + str(number_of_tries - self.currentline)
                        sent = s.sendto(message.encode(), multicast_group)
                    chkbtn.disabled = True
                else:
                    if (self.currentline > 0):
                        self.children[self.currentline].disabled = True
                        self.currentline = self.currentline - 1
                        self.children[self.currentline].disabled = False

                        self.children[self.currentline].children[number_of_letters - 1].focus = True
                        self.children[self.currentline].children[number_of_letters - 1].background_color = cell_empty
                        self.children[self.currentline].children[number_of_letters - 1].cursor_color = cell_empty

                    else:
                        self.children[self.currentline].disabled = True
                        self.parent.user_message = 'Game Over! You lost! Word was ' + target_word
                        self.parent.meaning_message = meaning_message
                        if svgame and not chkbtn.disabled:
                            message = "result" + "F" + myp.uname.text
                            sent = s.sendto(message.encode(), multicast_group)
                        chkbtn.disabled = True
        else:
            self.parent.user_message = "Too short! Try again"
            self.children[self.currentline].children[number_of_letters - 1].focus = True
            self.children[self.currentline].children[number_of_letters - 1].background_color = cell_empty
            self.children[self.currentline].children[number_of_letters - 1].cursor_color = cell_empty


class RemainingLettersForm(StackLayout):
    def InitializeRMLForm(self):
        self.clear_widgets()
        for letter in charset.keys():
            nextletter = Label(text=letter, size_hint=(0.15, 0.15), font_size=dp(20),
                               font_name=resource_path("fonts/OpenSans-Medium.ttf"))
            self.add_widget(nextletter)

    def updateletters(self):
        for i in self.children:
            match charset[i.text]:
                case 1:
                    with i.canvas.before:
                        Color(1,0,0,1)
                        Rectangle(size=(i.width, i.height), pos=i.pos)
                    i.color=(0,0,0,1)

                case 2:
                    with i.canvas.before:
                        Color(1,234/255,0,1)
                        Rectangle(size=(i.width, i.height), pos=i.pos)
                    i.color=(0,0,0,1)
                case 3:
                    with i.canvas.before:
                        Color(0,234/255,0,1)
                        Rectangle(size=(i.width, i.height), pos=i.pos)
                    i.color=(0,0,0,1)



if __name__ == '__main__':
    MyWordle().run()
