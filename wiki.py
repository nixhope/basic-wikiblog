from google.appengine.ext import db
from google.appengine.api import memcache
import webapp2
import jinja2
import logging

from handler import Handler
import authentication

class WikiPage(db.Model):
	title = db.StringProperty(required = True) # 500 chars max
	content = db.TextProperty(required = True) 
	url = db.StringProperty(required = True) # NOT UNIQUE
	created = db.DateTimeProperty(auto_now_add = True)
	author = db.StringProperty(required = True)
	# Duplicate url indicates edit

class Wiki(Handler):			
	def get(self):
		self.redirect('/wiki/wiki')		

def get_wiki(link, update=False, id=None, handler=None):
	key = '/wiki/%s'%link
	if id:
		key = '/wiki/%s/%s'%(link,id)
	wiki = memcache.get(key)
	if update or not wiki:
		if id:
			if not id.isdigit(): # Fake history
				return
			wiki = WikiPage.get_by_id(int(id))
			if not wiki or wiki.url != link: # Fake history
				return
		else:
			logging.warning('Querying datastore: SELECT [1] FROM WikiPage WHERE url=%s'%link)
			wiki = db.GqlQuery('SELECT * FROM WikiPage WHERE url=:1 '
				'ORDER BY created DESC LIMIT 1', link).get()
		if not wiki:
			wiki = link # Want to memcache db misses
		memcache.set(key, wiki)	
	if wiki == link:
		return None
	else:
		return wiki		
		
class Page(Handler):
	def get(self, link):
		id = self.request.get('history') # Edit
		wiki = get_wiki(link, id = id, handler=self)
		if wiki:
			self.render('wiki.html', title=wiki.title,
				content=wiki.content, url=link, created=wiki.created,
				author=wiki.author, version = wiki.key().id())
		else:
			self.redirect('/wiki/_edit/%s'%link)
		
class EditPage(Handler):
	def get(self, link):		
		username = authentication.getUserName(self)
		if username:
			if link in ['_edit', '_history']: # easter egg
				self.redirect('/wiki/meta')
				return
			id = self.request.get('history') # Edit
			wiki = get_wiki(link, id = id, handler=self)
			title = wiki.title if wiki else link.capitalize()
			content = wiki.content if wiki else ''
			url = link
			version = wiki.key().id() if wiki else ''
			self.render('wiki_edit.html', title=title,
				content = content, url = link, version = version)
		else:
			self.redirect('/login?redirect=%s'%self.request.url)
		
	def post(self, link):
		username = authentication.getUserName(self)
		if username:
			title = self.request.get('title')
			if not title:
				title = link
			content = self.request.get('content')
			version = self.request.get('version')				
			if title and content:
				wiki = WikiPage(title=title,
					content=content, url=link,
					author=username)
				logging.warning('Inserting WikiPage url: %s'%link)
				wiki.put()				
				get_wiki(link, update=True)
				get_history(link, update=True)
				self.redirect('/wiki/%s'%link)
			else:
				error = 'Both title and content are required!'
				self.render('wiki_edit.html', title=title,
				content = content, url = link, error=error,
				version = version)
		else:
			self.redirect('/login?redirect=%s'%self.request.url)
			
def get_history(link, update=False):
	key = '/wiki/_history/%s'%link
	wikis = memcache.get(key)
	if update or not wikis:
		logging.warning('Querying datastore: SELECT [all] FROM WikiPage WHERE url=%s'%link)
		wikis = list(db.GqlQuery('SELECT * FROM WikiPage WHERE url=:1 '
			'ORDER BY created DESC', link))
		if not wikis:
			wikis = link # Want to memcache db misses
		memcache.set(key, wikis)	
	if wikis == link:
		return None
	else:
		return wikis
		
class HistoryPage(Handler):
	def get(self, link):
		if link in ['_edit', '_history']: # easter egg
			self.redirect('/wiki/meta')
			return
		wikis = get_history(link)
		if wikis:
			self.render('wiki_history.html', url=link, wikis=wikis)
		else:
			self.throw_error(404)

