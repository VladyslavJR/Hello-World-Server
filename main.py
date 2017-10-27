import cgi

from google.appengine.api import users
import webapp2


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("""
                  <html>
                    <body>
                      <form method="get">
                        <div><textarea name="content" rows="3" cols="60"></textarea></div>
                        <div><input type="submit" value="Sign Guestbook"></div>
                      </form>
                    </body>
                  </html>""")

    def post(self):
        self.response.out.write(cgi.escape(self.request.get('content')))

    def add_post(self):
        self.response.out.write('<html><body>Hello</body></html>')


class GuestBook(webapp2.RequestHandler):
    def post(self):
        self.response.out.write('<html><body>You wrote:<pre>')
        self.response.out.write(cgi.escape(self.request.get('content')))
        self.response.out.write('</pre></body></html>')


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign', GuestBook),
], debug=True)


def main():
    from paste import httpserver
    httpserver.serve(app, host='127.0.0.1', port='8000')


if __name__ == '__main__':
    main()
