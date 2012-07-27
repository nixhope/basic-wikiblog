import re
import os

import jinja2
import webapp2
from google.appengine.ext import db
from google.appengine.api import users, memcache

from handler import Handler, ErrorHandler, SlashRedirect
import blog
import wiki
import login
import authentication

class Main(Handler):
	def get(self):
		self.render('base.html')
		
class Echo(Handler):
	'''Echo server'''
	def get(self):
		self.render('echo.html', lines=str(self.request).split('\r\n'))
		
	def post(self):
		self.write('echo.html', lines=str(self.request).split('\r\n'))
		
# Define which urls to handle and how
PAGE_RE = r'((?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([
		#Adding /? after everything allows for an option trailing slash
		('(.*)//+', SlashRedirect),
		('/', Main),
		('/blog/newpost/?', blog.NewPost),
		('/blog/p/(\d+).json', blog.PostJson),
		('/blog/p/(\d+)', blog.Post),
		('/blog/?.json', blog.BlogJson),		
		('/blog/?', blog.Blog),

		('/echo/?', Echo),

		('/login/?', login.Login),
		('/signup/?', login.Signup),
		('/logout/?', login.Logout),
		('/welcome/?', login.Welcome),
		
		# Wiki
		('/wiki/?', wiki.Wiki),		
		('/wiki/_edit/(\w+)/?', wiki.EditPage),
		('/wiki/_history/(\w+)/?', wiki.HistoryPage),
		('/wiki/(\w+)/?', wiki.Page),
		('/(.*)', ErrorHandler)
		], debug=True)