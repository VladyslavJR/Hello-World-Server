import webapp2
import subprocess
import argparse
import handlers

parser = argparse.ArgumentParser()

parser.add_argument('-hn', '--hostname', dest='HOST', default="localhost", help="Host", type=str)
parser.add_argument('-p', '--port', dest='PORT', default=9009, help="Server's port", type=int)
parser.add_argument('-rb', '--receive_buffer', dest="RECV_BUFFER", default=4096,
                    help="Receive buffer size", type=int)

args = parser.parse_args()

config = {
    'HOST': args.HOST,
    'PORT': args.PORT,
}

app = webapp2.WSGIApplication([
    ('/', handlers.MainPage),
], debug=True, config=config)


def main():
    subprocess.Popen('python ./chat_server.py -hn ' + str(args.HOST) + ' -p ' + str(args.PORT) +
                     ' -rb ' + str(args.RECV_BUFFER))

    from paste import httpserver

    httpserver.serve(app, host=args.HOST, port=(args.PORT + 1))


if __name__ == '__main__':
    main()
