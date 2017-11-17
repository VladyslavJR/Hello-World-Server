import webapp2
import handlers
import chat_server
import multiprocessing


app = webapp2.WSGIApplication([
    ('/', handlers.MainPage),
], debug=True)


def main():
    from paste import httpserver

    #httpserver.serve(app, host='localhost', port=9008)
    httpserver.server_runner(app, )


if __name__ == '__main__':
    pool = multiprocessing.Pool(processes=1)
    pool.apply(func=main)
    process = multiprocessing.Process(target=chat_server.start_server())

    pool.terminate()
