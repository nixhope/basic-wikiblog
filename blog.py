import json

from google.appengine.ext import db
from google.appengine.api import memcache
import webapp2

from handler import Handler
import authentication

class BlogPost(db.Model):
	title = db.StringProperty(required = True) # 500 chars max
	content = db.TextProperty(required = True) 
	created = db.DateTimeProperty(auto_now_add = True)
	author = db.StringProperty(required = False)
	def __str__(self):
		return str(self.key().id())+' '+self.title+' '+str(self.created)+':'+self.content

class NewPost(Handler):
	'''Deals with new posts'''
	def get(self):
		'''Provides form for new post'''
		username = authentication.getUserName(self)
		if username:
			self.render('blog_newpost.html',
				title='', content='', error='', username=username)
		else:
			self.redirect('/login?redirect=%s'%self.request.url)
		
	def post(self):
		'''Creates a new post'''
		username = authentication.getUserName(self)
		if username:
			title = self.request.get('subject')
			content = self.request.get('content')
			if title and content:
				p = BlogPost(title = title,
					content = content, author = username)
				p.put()
				id = str(p.key().id())
				get_single(id) # Fill memcache
				update_all()			
				self.redirect("/blog/p/"+id)
			else:
				error = 'Both title and content are required!'
				self.render('blog_newpost.html',
					title = title, content = content,
					error = error, username = username)
		else:
			self.redirect('/login?redirect=%s'%self.request.url)

def get_single(id):
	key = 'blog/p/%s'%id
	post = memcache.get(key)
	# We want to store non-existent IDs in memcache,
	# even if datastore query would return NoneType
	if not post:
		post = BlogPost.get_by_id(int(id))
		if not post:
			post = id # No such post, can't use None/False due to check above
		memcache.set(key, post)
	if post == id:
		return None
	else:
		return post

class Post(Handler):
	'''Deals with individual posts'''
	def get(self, id):
		'''Gets a particular post'''
		p = get_single(id)
		if p:
			self.render('blog_home.html', posts=[p])
		else:
			self.throw_error(404)

def update_all():
	'''Updates memcache using gets and cas'''
	# Not useful, since GAE doesn't support CAS	
	key = 'blog'
	query = list(db.GqlQuery('SELECT * FROM BlogPost '
		'ORDER BY created DESC LIMIT 10'))
	memcache.set(key, query)
#	r = False
#	while not r:
#		# IDEA: include some sort of timer to prevent infinites
#		val, u = memcache.gets(key)
#		r = memcache.cas(key, val, u)
			
def get_all():
	key = 'blog'
	recent_posts = memcache.get(key)
	if not recent_posts:
		recent_posts = list(db.GqlQuery('SELECT * FROM BlogPost '
				'ORDER BY created DESC LIMIT 10'))
		memcache.set(key, recent_posts)
	return recent_posts

class Blog(Handler):			
	def get(self):
		'''Gets the homepage (10 most recent posts)'''
		posts = get_all()
		self.render('blog_home.html', posts=posts)

def post_to_dict(post):
	'''Takes a BlogPost and returns a dict'''
	d = {}
	d['title'] = post.title
	d['created'] = post.created.strftime("%a %B %d %H:%M:%S %Y")
	d['content'] = post.content
	d['author'] = post.author if post.author else 'Anon'
	return d
		
class PostJson(Handler):
	''''''
	def get(self, id):
		post = get_single(id)
		if post:
			self.response.headers['Content-Type'] =	'application/json'
			self.write(json.dumps((post_to_dict(post))))
		else:
			self.throw_error(404)

class BlogJson(Handler):
	''' '''
	def get(self):
		all = list((post_to_dict(p) for p in get_all()))
		self.response.headers['Content-Type'] =	'application/json'
		self.write(json.dumps(all))
		