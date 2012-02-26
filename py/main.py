import os
import sys
import logging
from urllib import urlencode

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from django.utils import simplejson as json
from google.appengine.ext import db

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'httplib2'))

from httplib2 import Http
from models import Authorization

CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'

# Home page, displays the current Banter user's username and avatar 
# if they are authenticated, otherwise redirects to banters.com/oauth
# for authorization
class Main(webapp.RequestHandler):
    def get(self):
        ip = self.request.remote_addr
        auth = Authorization.all().filter('ip = ', ip).get()

        if not auth:
            data = dict(client_id=CLIENT_ID, response_type='code')
            url = "https://banters.com/oauth/authorize?%s" % urlencode(data)
            self.redirect(url)
            return
        
        # Retrieve data about the current user
        data = dict(oauth_token=auth.token)
        url = "https://banters.com/oauth/me.json?%s" % urlencode(data)
        resp, content = Http().request(url, "GET")
        data = json.loads(content)
        
        path = os.path.join(os.path.dirname(__file__), '../html/index.html')
        self.response.out.write(template.render(path, {
            'username': data["username"],
            'avatar': data["profile_photo"]["small"]
        }))
             
class OAuthHandler(webapp.RequestHandler):
    def get(self):
        if self.request.get('code'):

            data = dict(code=self.request.get('code'),  
                        client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        grant_type="authorization_code")

            resp, content = Http().request(
                "https://banters.com/oauth/access_token",
                "POST", 
                urlencode(data))

            if resp['status'] == '200':
                access_token = json.loads(content)["access_token"]
                auth = Authorization(ip=self.request.remote_addr, 
                                     token=access_token).put()
                self.redirect("/")
            else:
                print content # Check for error description
    
# simply here to suppress 404's on our dashboard from GAE hitting this URL
class WarmupHandler(webapp.RequestHandler):
    def get(self):
        logging.info('Warmup Request') 

 
application = webapp.WSGIApplication([('/', Main),
                                      ('/oauth', OAuthHandler)]
                                      , debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()