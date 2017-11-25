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


class ServerProtocol(WebSocketServerProtocol):
    def onOpen(self):
        self.factory.register(self)
        self.factory.broadcast_history_to_client(self)

    def connectionLost(self, reason):
        self.factory.unregister(self)

    def onConnect(self, request):
        print("Some request connected {}".format(request))

    def onMessage(self, payload, isBinary):
        if payload[0] is '\n'[0]:
            self.factory.authenticate(self, payload)
        elif payload.__len__() < 3 or payload[2] is not '\n'[0]:
            self.factory.broadcast_to_all(self, payload)


class ChatFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super(ChatFactory, self).__init__(*args, **kwargs)
        self.clients = []
        self.messages = []
        self.users = {}

    def register(self, client):
        self.clients.append(client)

    def authenticate(self, client, payload):
        user_name = payload[1:]
        self.users[client.peer] = {"object": client, "user_name": user_name}
        print("User " + user_name + " has authenticated.")
        self.broadcast_to_all(client, '', is_login=True)

    def unregister(self, client):
        if client.peer in self.users:
            self.log_out(client)
        if client in self.clients:
            self.clients.remove(client)

    def log_out(self, client):
        print("User " + self.users[client.peer]["user_name"] + " has loged out.")
        self.broadcast_to_all(client, '', is_logout=True)
        self.users.pop(client.peer)

    def broadcast_history_to_client(self, client):
        for msg in self.messages:
            client.sendMessage(msg)

    def broadcast_to_all(self, client, payload, is_logout=False, is_login=False):
        for c in self.clients:
            if c.peer in self.users:
                if self.users[c.peer]["object"] is client:
                    if is_logout:
                        msg = 'User ' + self.users[c.peer]["user_name"] + ' is offline.'
                    elif is_login:
                        msg = 'User ' + self.users[c.peer]["user_name"] + ' has joined our chat.'
                    else:
                        msg = '[' + self.users[c.peer]["user_name"] + '] ' + payload
                    self.messages.append(msg)
                    break
        for c in self.clients:
            if c.peer in self.users:
                self.users[c.peer]["object"].sendMessage(msg)


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
