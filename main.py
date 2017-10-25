import webapp2
import datetime


class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.write('Time: %s' % self.time_get())

    def time_get(self):
        return 'Now: %s' % datetime.datetime.now().__str__()


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
