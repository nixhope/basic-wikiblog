import re

import webapp2
import jinja2
from google.appengine.ext import db
from google.appengine.api import users

from handler import Handler
import authentication
		
providers = {
    'Google': 'www.google.com/accounts/o8/id', # shorter alternative: "Gmail.com"
    'MyOpenId': 'myopenid.com',
    'Yahoo' : 'yahoo.com',
    'MySpace' : 'myspace.com',
    'AOL' : 'aol.com'
}

class Signup(Handler):
	def render_signup(self, username = '', password = '',
				verify = '', email = '', usernameerror = '',
				passworderror = '', verifyerror = '',
				emailerror = '', redirect = ''):
		current_url = self.request.url
		user = authentication.getUser(self)
		if not redirect:
			redirect = '/welcome'
		p = {}
		for name, uri in providers.items():
			p[name] = users.create_login_url(dest_url=redirect,
				federated_identity=uri)
		self.render('signup.html',
			providers = p, username = username, password = password,
			verify = verify, email = email, usernameerror = usernameerror,
			passworderror = passworderror, verifyerror = verifyerror,
			emailerror = emailerror, redirect = redirect
		)
		
	def get(self):
		redirect = str(self.request.get('redirect'))
		self.render_signup(redirect = redirect)
			
	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		verify = self.request.get('verify')
		email = self.request.get('email')
		usernameerror = ''
		if not re.compile(r'^[a-zA-Z0-9_-]{3,20}$').match(username):
			usernameerror = 'Username must consist of 3-20 alphanumeric characters.'
		elif authentication.User.get_by_key_name(username):
			usernameerror = 'That user already exists'
		passworderror = '' if re.compile('^.{3,20}$').match(password) \
			else 'Password must be 3 to 20 characters long.'
		verifyerror = '' if password == verify \
			else 'Passwords did not match.'
		emailerror = 'Not a valid email address.' if \
			(email and not re.compile('^[\S]+@[\S]+\.[\S]+$').match(email)) else ''
		if (usernameerror+passworderror+verifyerror+emailerror):
			self.render_signup(username = username, password = password,
				verify = verify, email = email, usernameerror = usernameerror,
				passworderror = passworderror, verifyerror = verifyerror,
				emailerror = emailerror)
		else:
			user = authentication.User(key_name = username,
				email = email, password = authentication.hashText(password, 3),
				ip = self.request.remote_addr)
			authentication.setCookie(self, username)
			user.put()
			redirect = str(self.request.get('redirect'))
			if redirect:
				self.redirect(redirect)
			else:
				self.redirect('/welcome')
			
class Login(Handler):
	def render_login(self, username = '', password = '', error = '', redirect = ''):
		if not redirect:
			redirect = '/welcome'
		p = {}
		for name, uri in providers.items():
			p[name] = users.create_login_url(dest_url=redirect,
				federated_identity=uri)
		
		self.render('login.html',
			providers = p, username = username, password = password,
			error = error, redirect = redirect
		)
			
	def get(self):
		redirect = str(self.request.get('redirect'))
		self.render_login(redirect = redirect)
			
	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')
		redirect = str(self.request.get('redirect'))
		if re.compile(r'^[a-zA-Z0-9_-]{3,20}$').match(username) \
			and authentication.login(username, password):
			authentication.setCookie(self, username)
			if redirect:
				self.redirect(redirect)
			else:
				self.redirect('/welcome')
		else:
			self.render_login(username = username, password = password,
				error = 'Invalid details')

class Welcome(Handler):
	def get(self):
		username = authentication.getUserName(self)
		if username:
			self.render('welcome.html', name=username)
		else:
			self.redirect('/login')	
		
class Logout(Handler):
	def get(self):
		redirect = str(self.request.get('redirect'))
		if not redirect:
			redirect = '/'
		user = authentication.getUser(self)
		if user and user.openID:
			redirect = users.create_logout_url(redirect)
		authentication.deleteCookie(self)
		self.redirect(redirect)