import webapp2

from blog import *
from users import *

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/signup', Signup),
    ('/login', Login),
    ('/logout', Logout),

    ('/blogs/?', MyBlogs),
    ('/blogs/new', NewBlog),
    ('/blogs/([0-9]+)', BlogPage),

    ('/posts/new', NewPost),
    ('/posts/([0-9]+)', PostPage),
], debug=True)
