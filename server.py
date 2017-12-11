# coding=utf-8
import sys
import argparse
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

parser.add_argument('-p', '--port', dest="PORT", default=80, type=int)
parser.add_argument('-l', '--local', dest="local", default=False, type=bool)

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
            if payload[0] is '\n'[0]:
                self.factory.authenticate(self, payload)
            elif payload[0] is '\r'[0]:
                self.factory.register_user(self, payload)
            else:
                if payload in echo:
                    self.factory.broadcast_to_all(self, payload, tag='echo')
                else:
                    self.factory.broadcast_to_all(self, payload)


class User:
    def __init__(self, client=None, user_name='', password='', status='user'):
        if status is 'anonymous':
            self.user_name = 'Anonymous'
            self.password = ''
        else:
            self.user_name = user_name
            self.password = password
            if status is 'user':
                users.append(self)
                self.id = users.__len__() - 1
            elif status is 'admin':
                admins.append(self)
                self.id = admins.__len__() - 1
        self.client = client
        self.status = status

    def __del__(self):
        if self.status is 'user':
            users.remove(self)
        elif self.status is 'admin':
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
        dif_at = payload.find('\\', 1, payload.__len__() - 1)
        user_name = payload[1:dif_at]
        if user_name == 'John Doe':
            user = User(client, status='anonymous')
            self.online_anons.append(user)
            self.on_login(user)
        else:
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
                password = payload[dif_at + 1:]
                if user_name in admin_names:
                    user = User(client, user_name, password, status='admin')
                    self.online_admins.append(user)
                else:
                    user = User(client, user_name, password, status='user')
                    self.online_users.append(user)
                self.on_login(user)
            else:
                self.broadcast_to_all(client, user_name)
                client.sendClose(code=3010, reason=u'Username already taken')

    def authenticate(self, client, payload):
        payload = payload.decode('utf-8')
        dif_at = payload.find('\\', 1, payload.__len__() - 1)
        user_name = payload[1:dif_at]
        if user_name == 'John Doe':
            self.register_user(client, payload)
        else:
            password = payload[dif_at + 1:]
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
                if is_admin:
                    self.online_admins.append(user)
                else:
                    self.online_users.append(user)
                self.on_login(user)
            elif error_code == 0:
                self.broadcast_to_all(client, user_name)
                client.sendClose(code=3000, reason=u'No user with that name')
            elif error_code == 1:
                self.broadcast_to_all(client, user_name)
                client.sendClose(code=3001, reason=u'User already online')
            elif error_code == 2:
                self.broadcast_to_all(client, user_name)
                client.sendClose(code=3002, reason=u'Incorrect password')
            else:
                self.broadcast_to_all(client, user_name)
                client.sendClose(code=1000, reason=u'Unknown error')

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
        if not user_found:
            for anon in self.online_anons:
                if anon.client is client:
                    self.log_out(anon, status='anonymous')
                    break
        if client in self.clients:
            self.clients.remove(client)

    def log_out(self, user, status):
        print("User " + user.user_name + " has loged out.")
        self.broadcast_to_all(user.client, '', tag='logout')
        if status is 'user':
            self.online_users.remove(user)
        elif status is 'admin':
            self.online_admins.remove(user)
        elif status is 'anonymous':
            self.online_anons.remove(user)

    def on_login(self, user):
        print("User " + user.user_name + " has authenticated.")
        self.broadcast_history_to_client(user.client)
        self.broadcast_to_all(user.client, '', tag='login')

    def broadcast_history_to_client(self, client):
        for msg in self.messages:
            client.sendMessage(msg)

    def broadcast_to_all(self, client, payload, tag=''):
        msg = ''
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
                    if tag == 'logout':
                        msg = 'User ' + user.user_name + ' has left our chat.'
                    elif tag == 'login':
                        msg = 'User ' + user.user_name + ' has joined our chat'
                    else:
                        msg = '[' + user.user_name + '] ' + payload
                    if msg is not '':
                        self.messages.append(msg)
                    break
            if not user_found:
                for admin in self.online_admins:
                    user_found = True
                    if client is admin.client:
                        if tag == 'logout':
                            msg = 'Admin ' + admin.user_name + ' has left our chat.'
                        elif tag == 'login':
                            msg = 'Admin ' + admin.user_name + ' has joined our chat'
                        else:
                            msg = '[' + admin.user_name + '] ' + payload
                        if msg is not '':
                            self.messages.append(msg)
                        break
            if not user_found:
                for anon in self.online_anons:
                    if client is anon.client:
                        if tag == 'logout':
                            msg = 'Anonymous user has left our chat.'
                        elif tag == 'login':
                            msg = 'Anonymous user has joined our chat'
                        else:
                            msg = '[Anonymous] ' + payload
                        if msg is not '':
                            self.messages.append(msg)
                        break
        for user in self.online_users:
            user.client.sendMessage(msg)
        for admin in self.online_admins:
            admin.client.sendMessage(msg)
        for anon in self.online_anons:
            anon.client.sendMessage(msg)


if __name__ == "__main__":
    log.startLogging(sys.stdout)

    root = File(".")

    if not args.local:
        factory = ChatFactory(u"ws://sleepy-river-62121.herokuapp.com/")
    else:
        factory = ChatFactory(u"ws://127.0.0.1:8080/")
    factory.protocol = ServerProtocol
    resource = WebSocketResource(factory)
    root.putChild(u"ws", resource)

    site = Site(root)
    reactor.listenTCP(args.PORT, site)
    reactor.run()
