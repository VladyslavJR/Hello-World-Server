import webapp2
import subprocess
import argparse
import handlers


server_running = False


parser = argparse.ArgumentParser()

parser.add_argument('-hn', '--hostname', dest='HOST', default="localhost", help="Host", type=str)
parser.add_argument('-cp', '--chat_port', dest='CHAT_PORT', default=9009, help="Chat port", type=int)
parser.add_argument('-sp', '--site_port', dest='SITE_PORT', default=9010, help="Site port", type=int)
parser.add_argument('-rb', '--receive_buffer', dest="RECV_BUFFER", default=4096,
                    help="Receive buffer size", type=int)

args = parser.parse_args()


config = {
        'HOST': args.HOST,
        'PORT': args.CHAT_PORT,
    }


app = webapp2.WSGIApplication([
        ('/', handlers.MainPage),
    ], debug=True, config=config)


def main():
    subprocess.Popen("python chat_server.py -hn " + str(args.HOST) + " -cp " + str(args.CHAT_PORT) +
                     " -rb " + str(args.RECV_BUFFER))

    from paste import httpserver

    httpserver.serve(app, host=args.HOST, port=args.SITE_PORT)


if __name__ == '__main__':
    main()
