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
        self.factory.unregister_client(self)

    def onConnect(self, request):
        print("Some request connected {}".format(request))

    def onMessage(self, payload, isBinary):
        if payload.__len__() > 0:
            msg = json.loads(payload)
            if msg["type"] == "message":
                if msg["text"] in echo:
                    self.factory.broadcast_to_all(self, msg, tag='echo')
                else:
                    self.factory.broadcast_to_all(self, msg)
            elif msg["type"] == "authenticate":
                msg["password"] = "1234"
                self.factory.authenticate(self, msg)
            elif msg["type"] == "register":
                msg["password"] = "1234"
                self.factory.register_user(self, msg)
                    


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
        self.online_anons = []

    def register_client(self, client):
        self.clients.append(client)

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
            client.sendMessage(json.dumps(msg))
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
            client.sendMessage(json.dumps(msg))
            if is_admin:
                self.online_admins.append(user)
            else:
                self.online_users.append(user)
            self.on_login(user)
        elif error_code == 0:
            self.broadcast_to_all(client, user_name)
            msg = {
                "type":"authfailed",
                "reason":"nouser"
            }
            client.sendMessage(json.dumps(msg))
        elif error_code == 1:
            self.broadcast_to_all(client, user_name)
            msg = {
                "type":"authfailed",
                "reason":"nameinuse"
            }
            client.sendMessage(json.dumps(msg))
        elif error_code == 2:
            self.broadcast_to_all(client, user_name)
            msg = {
                "type":"authfailed",
                "reason":"invalidpassword"
            }
            client.sendMessage(json.dumps(msg))
        else:
            self.broadcast_to_all(client, user_name)
            msg = {
                "type":"authfailed",
                "reason":"unknown"
            }
            client.sendMessage(json.dumps(msg))

    def unregister_client(self, client):
        user_found = False
        for user in self.online_users:
            if client is user.client:
                self.log_out(user, status='user')
                user_found = True
                break
        if not user_found:
            for admin in self.online_admins:
                user_found = True
                if client is admin.client:
                    self.log_out(admin, status='admin')
                    break
        if client in self.clients:
            self.clients.remove(client)

    def log_out(self, user, status):
        print("User " + user.user_name + " has logged out.")
        self.broadcast_to_all(user.client, '', tag='logout')
        if status == 'user':
            self.online_users.remove(user)
        elif status == 'admin':
            self.online_admins.remove(user)

    def on_login(self, user):
        print("User " + user.user_name + " has authenticated.")
        self.broadcast_history_to_client(user.client)
        self.broadcast_to_all(user.client, '', tag='login')

    def broadcast_history_to_client(self, client):
        for msg in self.messages:
            client.sendMessage(msg)

    def broadcast_to_all(self, client, payload, tag=''):
        msg = ''
        user_name = ""
        if tag == 'echo':
            self.broadcast_to_all(client, payload)
            for admin in self.online_admins:
                if admin.user_name == 'Vlados':
                    msg = "...Portos..."
        else:
            user_found = False
            for user in self.online_users:
                if client is user.client:
                    user_found = True
                    user_name = user.user_name
                    if tag == 'logout':
                        msg = 'User ' + user.user_name + ' has left our chat.'
                    elif tag == 'login':
                        msg = 'User ' + user.user_name + ' has joined our chat'
                    else:
                        msg = payload["text"]
                    break
            if not user_found:
                for admin in self.online_admins:
                    user_found = True
                    user_name = admin.user_name
                    if client is admin.client:
                        if tag == 'logout':
                            msg = 'Admin ' + admin.user_name + ' has left our chat.'
                        elif tag == 'login':
                            msg = 'Admin ' + admin.user_name + ' has joined our chat'
                        else:
                            msg = payload["text"]
                        break

        if msg == "":
            return

        data = {
        "type":"message",
        "name":user_name,
        "text":msg,
        "date":str(datetime.now())
        }

        if data["name"] == "":
            data["name"] = "Server"

        msg = json.dumps(data)
        self.messages.append(msg)
        for user in self.online_users:
            user.client.sendMessage(msg)
        for admin in self.online_admins:
            admin.client.sendMessage(msg)


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
