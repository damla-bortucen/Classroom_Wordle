
# first of all import the socket library
import socket            
import struct
import gamesummary
import sys
import os

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
import threading
import json
from kivy.core.window import Window
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp

serverstarted = False
kw = ""


#the report popup, label and database to keep the scores
dbconn = gamesummary.initializedb()

class Scorepopup(Popup):
    
    pass

reportpopup = None


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



# listens to the following multicast address and port
multicast_group = '224.5.55.25'
server_address = ('', 15555)
 
# Create the socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind to the server address
sock.bind(server_address)
# Tell the operating system to add the socket to the multicast group
# on all interfaces.
group = socket.inet_aton(multicast_group)
mreq = struct.pack('4sL', group, socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)





class Teacher(App):

  def UdpServer(self, ibox, sttext, btn):

    global serverstarted
    global kw
    global dbconn

    def ServerProcess(sttext):
      
      global sock
      sttext.text = "Waiting for Clients"
      while True:
        try:
          msg, address = sock.recvfrom(1024)
          if msg.decode()=="quit server":
            sock.close()
            quit()
          elif msg.decode()=="Get Word":
            sock.sendto(kw.encode(), address)
          elif msg.decode()[:8]=="username":
            uname = msg.decode()[8:].upper()

            sttext.parent.children[1].children[0].text = sttext.parent.children[1].children[0].text + "\n" + '{} from {} connected'.format(uname, address[0]) + ',...Sending keyword to ' +  str(address)
            gamesummary.insertplayer(dbconn, uname, address[0])
          elif msg.decode()[:6]=="result" and msg.decode()[6]=="S":
            uname = msg.decode()[7:msg.decode().rfind(" ")].upper()
            nsteps = int(msg.decode()[msg.decode().rfind(" ")+1:])

            sttext.parent.children[1].children[0].text = sttext.parent.children[1].children[0].text + "\n" + '{} found the word in {} steps'.format(uname , str(nsteps)) 
            # score is total tries - the try user found the kewword
            gamesummary.insertscore(dbconn, uname, address[0], kw, 1, len(kw)-nsteps+1)
          elif msg.decode()[:6]=="result" and msg.decode()[6]=="F":
            uname = msg.decode()[7:].upper()

            sttext.parent.children[1].children[0].text = sttext.parent.children[1].children[0].text + "\n" + '{} failed...'.format(uname) 
            gamesummary.insertscore(dbconn, uname, address[0], kw, 0, 0)
        except KeyboardInterrupt:
          sock.close()
          quit()

    kw = ibox.text     
    if kw in wldict.keys() and not serverstarted:
      ibox.disabled = True
      x = threading.Thread(target=ServerProcess, args=(sttext,))
      serverstarted = True
      btn.disabled = True
      x.start()
      # Make sure server is stopped when right corner x is pressed
      Window.bind(on_request_close=self.closewindow)
    elif kw in wldict.keys() and serverstarted:
      sttext.text = "Waiting for Clients"
      btn.disabled = True
      ibox.disabled = True
    elif ibox.text == "":
      sttext.text = "Please enter a valid word"
      ibox.focus = True
    else:
      sttext.text = ibox.text + " is not found in dictionary, try again"
      ibox.text = ""
      ibox.focus = True
  def quitter(self):
    message = 'quit server'
    multicast_group = ("224.5.55.25", 15555)
    # Create UDP socket object
    sq = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    sent = sq.sendto(message.encode(), multicast_group)
    quit()
    
  def renewword(self, ibox, sttext, clist, btn):

    ibox.text = ""
    ibox.disabled = False
    sttext.text = "Please input the target word (5-9 letters)"
    clist.text =  "LIST OF CONNECTED CLIENTS"
    btn.disabled = False
    ibox.focus = True
  
  def closewindow(self, src):
    print(self, src)
    self.quitter()

  def showreport(self):
    global reportpopup

    if not reportpopup:
      reportpopup = Scorepopup()
      
    reportpopup.content_text.text = gamesummary.showresults(dbconn)
    reportpopup.open()


class InputBox(TextInput):
  def insert_text(self, substring, from_undo=False):
    s = substring.upper()
    if len(self.text) > 9:
      s = ""
    return super().insert_text(s, from_undo=from_undo)




Teacher().run()
