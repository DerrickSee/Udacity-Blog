import os
import hmac
import json

import webapp2
import jinja2

from models import *
from filters import *

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

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
jinja_env.filters['linebreaks'] = linebreaks


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

    def authenticate(self, redirect="/login"):
        # If user is not logged in, redirect to another page. Defaults to login page.
        if not self.user:
            return self.redirect(redirect)


class MainPage(BlogHandler):
    """
    Home Page of Multi User Blogs.
    View all recents posts on the platform.
    """
    def get(self):
        self.render('index.html', posts=Post.all().order('-created'))


class MyBlogs(BlogHandler):
    """
    View all blogs user created
    """
    def get(self):
        self.authenticate()
        blogs = Blog.all().filter(
            'created_by = ', self.user).order('-created')
        self.render('blog-list.html', blogs=blogs)


class NewBlog(BlogHandler):
    """
    Create a new blog
    """
    def get(self):
        self.authenticate()
        self.render('blog-form.html')

    def post(self):
        self.authenticate()
        title = self.request.POST.get('title')
        description = self.request.POST.get('description')
        # Create blog if all fields are valid
        if title and description:
            b = Blog(title=title, description=description, created_by=self.user)
            b.put()
            self.redirect('/blogs/%s' % str(b.key().id()))
        else:
            error = "Please enter title and description!"
            self.render("blog-form.html", title=title, description=description, error=error)


class BlogPage(BlogHandler):
    """
    View posts in a blog
    """
    def get(self, blog_id):
        blog = Blog.get_by_id(int(blog_id))
        if not blog:
            return self.render404()
        # Get all post in blog
        posts = Post.all().ancestor(blog).order('-created')
        self.render("blog.html", posts=posts, blog=blog)


class NewPost(BlogHandler):
    """
    Create a new post
    """
    def get(self):
        self.authenticate()
        blogs = Blog.all().filter('created_by = ', self.user)
        if blogs.count() == 0:
            self.redirect('/blogs/new')
        self.render('post-form.html', blogs=blogs, blog_id=self.request.GET.get('blog_id'))

    def post(self):
        self.authenticate()
        parent = self.request.POST.get('blog')
        subject = self.request.POST.get('subject')
        content = self.request.POST.get('content')
        # Create post if all fields are valid
        if parent and subject and content:
            parent = Blog.get_by_id(int(parent))
            p = Post(parent=parent.key(), subject=subject, content=content,
                     created_by=self.user)
            p.put()
            self.redirect('/blogs/%s/posts/%s' % (parent.key().id(), p.key().id()))
        else:
            error = "subject and content, please!"
            self.render("post-form.html", subject=subject, content=content, error=error)


class PostMixin():
    """
    Get blog and post via ids
    """
    def get_post(self, blog_id, post_id):
        blog = Blog.get_by_id(int(blog_id))
        post = Post.get_by_id(int(post_id), parent=blog)
        return post, blog


class PostPage(PostMixin, BlogHandler):
    """
    View Post.
    """
    def get(self, blog_id, post_id):
        post, blog = self.get_post(blog_id, post_id)
        if not post:
            return self.render404()
        # Get comments from post
        comments = Comment.all().ancestor(post).order('-created')
        self.render("post.html", post=post, blog=blog, comments=comments)

    # Post a comment on the post page
    def post(self, blog_id, post_id):
        # check if user is logged in
        self.authenticate()
        post, blog = self.get_post(blog_id, post_id, True)
        if not post:
            return self.render404()
        content = self.request.POST['content']
        # check if comment content is given
        if not content:
            error = "subject and content, please!"
            self.render("post.html", post=post, blog=blog, error=error)
        # Create comment then redirect back to post
        c = Comment(content=content, created_by=self.user, parent=post)
        c.put()
        self.redirect('/blogs/%s/posts/%s' % (blog_id, post_id))


class PostUpdate(PostMixin, BlogHandler):
    """
    Update Post.
    """
    def get(self, blog_id, post_id):
        self.authenticate()
        post, blog = self.get_post(blog_id, post_id)
        # Check if post was created by user
        if post is None or post.created_by.key() != self.user.key():
            return self.render404()
        blogs = Blog.all().filter('created_by = ', self.user)
        self.render("post-form.html", post=post, blog_id=blog_id, blogs=blogs,
                    subject=post.subject, content=post.content)

    def post(self, blog_id, post_id):
        self.authenticate()
        post, blog = self.get_post(blog_id, post_id, True, True)
        # Check if post was created by user
        if post is None or post.created_by.key() != self.user.key():
            return self.render404()
        subject = self.request.POST.get('subject')
        content = self.request.POST.get('content')
        # Check if form fields are filled up
        if subject and content:
            # Update post and redirect to page page
            post.subject = subject
            post.content = content
            post.put()
            self.redirect('/blogs/%s/posts/%s' % (blog_id, post_id))
        else:
            error = "subject and content, please!"
            blogs = Blog.all().filter('created_by = ', self.user)
            self.render("post-form.html", post=post, blog_id=blog_id, blogs=blogs,
                        subject=post.subject, content=post.content, error=error)


class PostDelete(PostMixin, BlogHandler):
    """
    Request to Delete Posts. DELETE only. Returns success_url for redirect.
    """
    def delete(self, blog_id, post_id):
        post, blog = self.get_post(blog_id, post_id, True, True)
        if post is None or self.user is None or post.created_by.key() != self.user.key():
            return self.render404()
        post.delete()
        # Create a json response with redirect url
        self.response.headers['Content-Type'] = 'application/json'
        obj = {'success_url': '/blogs/%s' % blog_id}
        return self.response.out.write(json.dumps(obj))


class PostLike(PostMixin, BlogHandler):
    """
    Request to Like Posts. POST only.
    """
    def post(self, blog_id, post_id):
        self.authenticate()
        post, blog = self.get_post(blog_id, post_id, True)
        # User that created the post cannot like the post
        if post is None or post.created_by.key() == self.user.key():
            return self.render404()
        # Append to/remove from likes base of Post value
        if self.request.POST.get('like') == 'like':
            post.likes.append(self.user.key())
        elif self.request.POST.get('like') == 'unlike':
            post.likes.remove(self.user.key())
        post.put()
        return self.redirect('/blogs/%s/posts/%s' % (blog_id, post_id))


class PostLikeList(BlogHandler):
    """
    A list of posts user liked
    """
    def get(self):
        self.authenticate()
        # Get all posts where user key is in the like attribute (list)
        posts = Post.gql("WHERE likes = :1", self.user.key())
        return self.render("post-like.html", posts=posts)
