import socket
import sys
import select
import re
import argparse


parser = argparse.ArgumentParser()

parser.add_argument('-hn', '--hostname', dest='HOST', default="0.0.0.0", help="Host", type=str)
parser.add_argument('-p', '--port', dest='PORT', default=9009, help="Server's port", type=int)
parser.add_argument('-rb', '--receive_buffer', dest="RECV_BUFFER", default=4096,
                    help="Receive buffer size", type=int)

args = parser.parse_args()


SOCKET_LIST = []
userNamePattern = re.compile(r'\[(?P<userName>[ a-zA-Z0-9]+)\](?P<msg>[ a-zA-Z0-9]+)')


def chat_server():

    messages = []

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((args.HOST, args.PORT))
    server_socket.listen(10)

    SOCKET_LIST.append(server_socket)

    print "Chat server started on " + str(server_socket.getsockname())

    while 1:

        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST, [], [], 0)

        for sock in ready_to_read:

            if sock == server_socket:
                sockfid, addr = server_socket.accept()
                SOCKET_LIST.append(sockfid)
                print " Client (%s, %s) connected" % addr

                msg = "\r" + "[%s:%s] entered our chatting room" % addr
                messages.append(msg)
                broadcast_to_all(server_socket, msg, sockfid)
                # Broadcast all messages to the new client
                for msg in messages:
                    broadcast_to_client(server_socket, sockfid, msg)

            else:
                try:
                    data = sock.recv(args.RECV_BUFFER)
                    if data:
                        if data[0] == 'p':
                            print "Ping from [" + str(sock.getpeername()) + "]"
                            continue
                        elif data[0] == 'm':
                            m = userNamePattern.match(data[1:])
                            if m:
                                msg = "\r" + '[' + m.group('userName') + '] ' + m.group('msg')
                            else:
                                msg = "\r" + '[' + str(sock.getpeername()) + '] ' + data[1:]
                            messages.append(msg)
                            broadcast_to_all(server_socket, msg, 0)
                    else:
                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)

                        print " Client (%s, %s) disconnected" % addr

                        msg = "\r" + "Client (%s, %s) is offline" % addr
                        messages.append(msg)
                        broadcast_to_all(server_socket, msg, 0)

                except:
                    print " Client (%s, %s) disconnected" % addr

                    msg = "\r" + "Client (%s, %s) is offline" % addr
                    messages.append(msg)
                    broadcast_to_all(server_socket, msg, 0)
                    continue

    server_socket.close()


def broadcast_to_all(server_socket, message, sock_to_avoid):
    for sock in SOCKET_LIST:
        if sock != server_socket and sock != sock_to_avoid:
            try:
                sock.send(message)
            except:
                sock.close()
                if sock in SOCKET_LIST:
                    SOCKET_LIST.remove(sock)


def broadcast_to_client(server_socket, sock, message):
    if sock != server_socket:
        try:
            sock.send(message)
        except:
            sock.close()
            if sock in SOCKET_LIST:
                SOCKET_LIST.remove(sock)


def start_server(port=9009):
    PORT = port
    chat_server()


if __name__ == "__main__":
    sys.exit(chat_server())
