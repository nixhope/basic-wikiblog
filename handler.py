import os

import webapp2
from google.appengine.ext import db
import jinja2

import authentication

class Handler(webapp2.RequestHandler):
	template_dir = os.path.join(
			os.path.dirname(__file__), 'templates')
	jinja_env = jinja2.Environment(
		loader = jinja2.FileSystemLoader(template_dir),
		autoescape = True)
	
	def write(self, *a, **kw):
		'''Writes directly to the http request'''
		self.response.out.write(*a, **kw)
		
	def render_str(self, template, **params):
		'''Returns a string of the rendered template'''
		t = self.jinja_env.get_template(template)
		return t.render(params)
		
	def render(self, template, **kw):
		'''Render using the template and parameters'''
		username = authentication.getUserName(self)
		self.write(self.render_str(template,
			_user=username, _url=self.request.url, **kw))
		
	def throw_error(self, code):
		'''Throws an error, e.g. 404'''
		self.response.set_status(code)
		message = 'An error was encountered. Terribly sorry.'
		if code == 403:
			message = 'Access denied. You do not have permission to access this resource.'\
			' Please do not try again'
		if code == 404:
			message = 'The page or resource you requested could not be found. '\
			'If you caught a broken link, please report it to the naughty admin.'
		self.render('error.html', errorcode=code, errormessage=message)

class ErrorHandler(Handler):
	''''''
	def get(self, params):
		self.throw_error(404)		
		
class SlashRedirect(Handler):
	'''Removes multiple trailing slashes and redirects'''
	def get(self, path):
		self.redirect(path)