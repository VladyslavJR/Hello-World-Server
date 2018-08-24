# coding=utf-8
import sys
import argparse
import json

import random

from datetime import datetime

from twisted.web.static import File
from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol

from autobahn.twisted.resource import WebSocketResource

reload(sys)
sys.setdefaultencoding('utf8')

parser = argparse.ArgumentParser()

parser.add_argument('-p', '--port', dest="PORT", default=8000, type=int)
parser.add_argument('-l', '--local', dest="local", action="store_true")

args = parser.parse_args()

admins = []
users = []

echo = ['vlados', 'Vlados', 'владос', 'Владос']
admin_names = ['Vlados']


class ServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register_client(self)

    def connectionLost(self, reason):
        if hasattr(self, 'user'):
            self.factory.unregister_user_client(self.user)
        else:
            self.factory.unregister_client(self)

    def onConnect(self, request):
        print("Some request connected {}".format(request))

    def onMessage(self, payload, isBinary):
        if payload.__len__() > 0:
            try:
                msg = json.loads(payload)
                if msg["type"] == "message":
                    if msg["text"] in echo:
                        self.factory.broadcast_to_all(self.user, msg, tag='echo')
                    else:
                        self.factory.broadcast_to_all(self.user, msg)
                elif msg["type"] == "authenticate":
                    msg["password"] = "1234"
                    self.factory.authenticate(self, msg)
                elif msg["type"] == "register":
                    msg["password"] = "1234"
                    self.factory.register_user(self, msg)
                elif msg["type"] == "pong":
                    self.factory.send_pong(self)
            except ValueError:
                print(str(payload))

    def assign_user(self, user):
        self.user = user
                    


class User:
    def __init__(self, client=None, user_name='', password='', status='user'):
        self.user_name = user_name
        self.password = password
        if status == 'user':
            users.append(self)
            self.id = users.__len__() - 1
        elif status == 'admin':
            admins.append(self)
            self.id = admins.__len__() - 1
        self.client = client
        self.status = status

    def sendMessage(self, msg):
        self.client.sendMessage(msg)

    def __del__(self):
        if self.status == 'user':
            users.remove(self)
        elif self.status == 'admin':
            admins.remove(self)


class ChatFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super(ChatFactory, self).__init__(*args, **kwargs)
        self.clients = []
        self.messages = []
        self.online_users = []
        self.online_admins = []

    def register_client(self, client):
        self.clients.append(client)

    def unregister_client(self, client):
        self.clients.remove(client)

    def register_user(self, client, payload):
        user_name = payload["name"]
        name_taken = False
        if user_name in admin_names:
            for t_admin in admins:
                if t_admin.user_name == user_name:
                    name_taken = True
                    break
        else:
            for t_user in users:
                if t_user.user_name == user_name:
                    name_taken = True
                    break
        if not name_taken:
            password = payload["password"]
            if user_name in admin_names:
                user = User(client, user_name, password, status='admin')
                self.online_admins.append(user)
            else:
                user = User(client, user_name, password, status='user')
                self.online_users.append(user)
            self.on_login(user)
            msg = {
                "type": "register"
            }
            client.assign_user(user)
            user.sendMessage(json.dumps(msg))
        else:
            msg = {
                "type":"regfailed",
                "reason":"nametaken"
            }

            client.sendMessage(json.dumps(msg))

    def authenticate(self, client, payload):
        user_name = payload["name"]
        password = payload["password"]
        error_code = 0
        user = None
        is_admin = user_name in admin_names
        if is_admin:
            for t_admin in admins:
                if user_name == t_admin.user_name:
                    if t_admin not in self.online_admins:
                        if password == t_admin.password:
                            user = t_admin
                            user.client = client
                            error_code = -1
                        else:
                            error_code = 2
                    else:
                        error_code = 1
                    break
        else:
            for t_user in users:
                if user_name == t_user.user_name:
                    if t_user not in self.online_users:
                        if t_user.password == password:
                            user = t_user
                            user.client = client
                            error_code = -1
                        else:
                            error_code = 2
                    else:
                        error_code = 1
                    break
        if error_code == -1:
            msg = {
                "type":"authenticated"
            }
            client.assign_user(user)
            user.sendMessage(json.dumps(msg))
            if is_admin:
                self.online_admins.append(user)
            else:
                self.online_users.append(user)
            self.on_login(user)
        elif error_code == 0:
            msg = {
                "type":"authfailed",
                "reason":"nouser"
            }
            client.sendMessage(json.dumps(msg))
        elif error_code == 1:
            msg = {
                "type":"authfailed",
                "reason":"nameinuse"
            }
            client.sendMessage(json.dumps(msg))
        elif error_code == 2:
            msg = {
                "type":"authfailed",
                "reason":"invalidpassword"
            }
            client.sendMessage(json.dumps(msg))
        else:
            msg = {
                "type":"authfailed",
                "reason":"unknown"
            }
            client.sendMessage(json.dumps(msg))

    def unregister_user_client(self, user):
        if user in self.online_users:
            self.log_out(user, status='user')
        elif user in self.online_admins:
            self.log_out(admin, status='admin')
        self.unregister_client(user.client)

    def log_out(self, user, status):
        print("User " + user.user_name + " has logged out.")
        self.broadcast_to_all(user, tag='logout')
        if status == 'user':
            self.online_users.remove(user)
        elif status == 'admin':
            self.online_admins.remove(user)

    def on_login(self, user):
        print("User " + user.user_name + " has authenticated.")
        self.broadcast_history_to_user(user)
        self.broadcast_to_all(user, tag='login')

    def broadcast_history_to_user(self, user):
        for msg in self.messages:
            user.sendMessage(msg)

    def send_pong(self, client):
        pong = {
            "type":"pong"
        }

        client.sendMessage(json.dumps(pong))

    def broadcast_to_all(self, user, payload='', tag=''):
        msg = ''
        user_name = ""
        if tag == 'echo':
            self.broadcast_to_all(user, payload)
            for admin in self.online_admins:
                if admin.user_name == 'Vlados':
                    msg = "...Portos..."
        elif tag == 'server':
            msg = payload['text']
        elif tag == 'login':
            msg = ('User ' if user in self.online_users else 'Admin ') + user.user_name + \
                   ' has joined our chat'
        elif tag == 'logout':
            msg = ('User ' if user in self.online_users else 'Admin ') + user.user_name + \
                   ' has joined our chat'
        else:
            msg = payload["text"]

        if msg == "":
            return

        data = {
        "type":"message",
        "name": user.user_name,
        "text":msg,
        "date": str(datetime.now()) if type(payload) is str else payload['date']
        }

        if tag == 'server' or tag == 'login' or tag == 'logout':
            data["name"] = "server"

        msg = json.dumps(data)
        self.messages.append(msg)

        for online_user in self.online_users:
            if online_user is not user:
                online_user.sendMessage(msg)
        for online_admin in self.online_admins:
            if online_admin is not admin:   
                online_admin.sendMessage(msg)


if __name__ == "__main__":
    log.startLogging(sys.stdout)

    root = File("client/")

    if not args.local:
        factory = ChatFactory(u"ws://sleepy-river-62121.herokuapp.com/")
    else:
        factory = ChatFactory(u"ws://127.0.0.1:8000/")
    factory.protocol = ServerProtocol
    resource = WebSocketResource(factory)
    root.putChild(u"ws", resource)

    site = Site(root)
    reactor.listenTCP(args.PORT, site)
    reactor.run()
