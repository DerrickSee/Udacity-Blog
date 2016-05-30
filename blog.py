import os
import re
import random
import hashlib
import hmac
from string import letters

import webapp2
import jinja2
from google.appengine.ext import db

from models import *
from filters import *

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

secret = 'udacity-project-2'

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new(secret, val).hexdigest())

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

jinja_env.filters['timesince'] = timesince

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        params['user'] = self.user
        return render_str(template, **params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)

    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def logout(self):
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))

    def render404(self):
        self.error(404)
        self.render('404.html')

def render_post(response, post):
    response.out.write('<b>' + post.subject + '</b><br>')
    response.out.write(post.content)

class MainPage(BlogHandler):
  def get(self):
      self.render('index.html', posts=Post.all().order('-created'))


def blog_key(name = 'default'):
    return db.Key.from_path('blogs', name)


class LoginRequired(BlogHandler):

    def authenticate(self, redirect="/login"):
        if not self.user:
            self.redirect(redirect)


class MyBlogs(BlogHandler):
    # def get(self):
    #     posts = greetings = Post.all().filter(
    #         'created_by = ', self.user).order('-created')
    #     self.render('blog.html', posts = posts)
    def get(self):
        blogs = Blog.all().filter(
            'created_by = ', self.user).order('-created')
        self.render('blog-list.html', blogs = blogs)


class NewBlog(LoginRequired):

    def get(self):
        self.authenticate()
        self.render('blog-form.html')

    def post(self):
        self.authenticate()
        title = self.request.POST.get('title')
        description = self.request.POST.get('description')
        if title and description:
            b = Blog(title = title, description = description, created_by = self.user)
            b.put()
            self.redirect('/blogs/%s' % str(b.key().id()))
        else:
            error = "Please enter title and description!"
            self.render("blog-form.html", title=title, description=description, error=error)



class BlogPage(BlogHandler):

    def get(self, blog_id):
        blog = Blog.get_by_id(int(blog_id))
        if not blog:
            self.error(404)
            return
        posts = Post.all().ancestor(blog).order('-created')
        self.render("blog.html", posts = posts, blog = blog)


class PostPage(BlogHandler):
    def get(self, blog_id, post_id):
        blog = Blog.get_by_id(int(blog_id))
        post = Post.get_by_id(int(post_id), parent=blog)

        if not post:
            return self.render404()
        self.render("post.html", post = post, blog=blog)

class NewPost(LoginRequired):
    def get(self):
        self.authenticate()
        blogs = Blog.all().filter('created_by = ', self.user)
        self.render('post-form.html', blogs=blogs, blog_id=self.request.GET.get('blog_id'))

    def post(self):
        self.authenticate()
        parent = self.request.get('blog')
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            parent = Blog.get_by_id(int(parent))
            p = Post(parent = parent.key(), subject = subject, content = content,
                     created_by=self.user)
            p.put()
            self.redirect('/blogs/%s/posts/%s' % (parent.key().id(), p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("newpost.html", subject=subject, content=content, error=error)
