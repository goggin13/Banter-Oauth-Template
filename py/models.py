from google.appengine.ext import db

class Authorization(db.Model):
   ip = db.StringProperty()
   token = db.StringProperty()