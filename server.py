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

    def connectionLost(self, reason):
        self.factory.unregister(self)

    def onConnect(self, request):
        print("Some request connected {}".format(request))

    def onMessage(self, payload, isBinary):
        if payload[0] is '\n'[0]:
            self.factory.authenticate(self, payload)
        elif payload.__len__() < 3 or payload[2] is not '\n'[0]:
            self.factory.broadcast_to_all(self, payload)


class User:
    def __init__(self, client, user_name, id_number):
        self.id = id_number
        self.user_name = user_name
        self.client = client


class ChatFactory(WebSocketServerFactory):
    def __init__(self, *args, **kwargs):
        super(ChatFactory, self).__init__(*args, **kwargs)
        self.clients = []
        self.messages = []
        self.users = []

    def register(self, client):
        self.clients.append(client)

    def authenticate(self, client, payload):
        user_name = payload[1:]
        name_taken = False
        for user in self.users:
            if user_name == user.user_name:
                name_taken = True
                break
        if not name_taken:
            self.users.append(User(client, user_name, self.users.__len__()))
            print("User " + user_name + " has authenticated.")
            self.broadcast_history_to_client(client)
            self.broadcast_to_all(client, '', tag='login')
        else:
            self.broadcast_to_all(client, user_name, tag='clone')
            client.sendClose(code=1000, reason=u'You shall not pass!')

    def unregister(self, client):
        for user in self.users:
            if client is user.client:
                self.log_out(user)
                break
        if client in self.clients:
            self.clients.remove(client)

    def log_out(self, user):
        print("User " + user.user_name + " has loged out.")
        self.broadcast_to_all(user.client, '', tag='logout')
        self.users.remove(user)

    def broadcast_history_to_client(self, client):
        for msg in self.messages:
            client.sendMessage(msg)

    def broadcast_to_all(self, client, payload, tag=''):
        if tag == 'clone':
            msg = 'Some unworthy being tried to impersonate ' + payload + ', but our Lord and Saviour ' \
                                                                          'The Saint Code has protected ' \
                                                                          'us from this menace. All hail ' \
                                                                          'The Saint Code!'
            self.messages.append(msg)
        else:
            for user in self.users:
                if client is user.client:
                    if tag == 'logout':
                        msg = 'Follower ' + user.user_name + ' has left our circle. Let The Saint Code be with him!'
                    elif tag == 'login':
                        msg = 'Follower ' + user.user_name + ' has joined our circle. Hail to The Saint Code!'
                    else:
                        msg = '[' + user.user_name + '] ' + payload
                    self.messages.append(msg)
                    break
        for user in self.users:
            user.client.sendMessage(msg)


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
