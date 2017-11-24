import sys
import argparse
from twisted.web.static import File
from twisted.python import log
from twisted.internet import reactor
from twisted.web.server import Site

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol

from autobahn.twisted.resource import WebSocketResource


parser = argparse.ArgumentParser()

parser.add_argument('-p', '--port', dest="PORT", default=8080, type=int)
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

    def onMessageFrame(self, payload):
        if payload.__len__() > 0:
            if payload[0][0] == '\n'[0]:
                self.factory.authenticate(self, payload[0])
            else:
                self.factory.broadcast_to_all(self, payload)

    def onMessage(self, payload, isBinary):
        print("Message received: " + str(payload))

    def onFrameData(self, payload):
        print("Data: " + str(payload))


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

    def unregister(self, client):
        if client.peer in self.users:
            self.log_out(client)
        if client in self.clients:
            self.clients.remove(client)

    def log_out(self, client):
        print("User " + self.users[client.peer]["user_name"] + " has loged out.")
        self.users.pop(client.peer)

    def broadcast_history_to_client(self, client):
        for msg in self.messages:
            client.sendMessage(msg)

    def broadcast_to_all(self, client, payload):
        for c in self.clients:
            if c.peer in self.users:
                if self.users[c.peer]["object"] is client:
                    msg = str(payload)
                    msg = msg[2:msg.__len__() - 2]
                    msg = '[' + self.users[c.peer]["user_name"] + '] ' + msg
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
