from google.appengine.api import users
import webapp2


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))


class SamplePage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text\plain'
        self.response.write("Hey there!")


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/hey/', SamplePage),
], debug=True)


def main():
    from paste import httpserver
    httpserver.serve(app, host='127.0.0.1', port='8000')


if __name__ == '__main__':
    main()
