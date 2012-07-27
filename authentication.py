from google.appengine.api import users
from google.appengine.ext import db
from bcrypt import bcrypt

def getUser(handler):
	'''Returns a User object, or None if the user is not authenticated'''
	user = users.get_current_user()
	if user:
		return User(key_name = user.nickname(),
			email = user.email(),
			openID = True)
	username = testCookie(handler)
	if username:
		return User.get_by_key_name(username)
	
def getUserName(handler):
	user = getUser(handler)
	if user:
		return user.key().name()
		
def hashText(text, iters = 2):
	'''Returns a hexhash of the text using bcrypt for n iterations'''
	# I don't actually know how reliable python bcrypt is
	# But compiled version is not an option with GAE
	return bcrypt.hashpw(text, bcrypt.gensalt(iters)).encode('hex')

def checkHash(text, hexhash):
	'''Checks if text matches hexhash'''
	h = hexhash.decode('hex')
	return bcrypt.hashpw(text, h) == h

def login(username, password):
	'''Returns User if user is valid'''
	user = User.get_by_key_name(username)
	if user and checkHash(password, user.password):
		return user

def setCookie(handler, username):
	'''Sets a cookie with the username and its hexhash'''
	username = str(username) # This may cause errors if users enter unicode, hopefully regex stops this
	hexhash = hashText(username, 1)
	s = str('%s|%s'%(username, hexhash))
	handler.response.headers.add_header('Set-Cookie',
		'username=%s; Path=/'%s)
	
def testCookie(handler):
	'''Returns username if the username cookie is legitimately set'''
	cookie = handler.request.cookies.get('username')
	if cookie:
		(username, h) = cookie.split('|')
		if checkHash(username, h):
			return username
		else:
			deleteCookie(handler)
		
def deleteCookie(handler):
	'''Deletes a cookie by making it expire in the past'''
	handler.response.headers.add_header('Set-Cookie',
		'username=; Path=/; Expires=Sat, 01 Jan 2011 10:12:24 GMT')
	
class User(db.Model):
	# name is key_name
	email = db.StringProperty(required = False)
	openID = db.BooleanProperty(required = False)
	password = db.StringProperty(required = False)
	joined = db.DateTimeProperty(auto_now_add = True, required=False)
	ip = db.StringProperty(required = False)
	def __str__(self):
		return self.key().name()+' '+self.email+' '+self.openID