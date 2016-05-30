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
    ('/blogs/([0-9]+)/posts/([0-9]+)', PostPage),
    ('/blogs/([0-9]+)/posts/([0-9]+)/update', PostUpdate),
    ('/blogs/([0-9]+)/posts/([0-9]+)/delete', PostDelete),

    ('/posts/new', NewPost),

], debug=True)
