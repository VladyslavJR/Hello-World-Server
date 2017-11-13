import webapp2
import chat_server


class MainPage (webapp2.RequestHandler):
    def get(self):
        self.response.write("Hello there! The chat's current port is " + str(chat_server.args.PORT))
