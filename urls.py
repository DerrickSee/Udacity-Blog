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
    ('/blogs/([0-9]+)/posts/([0-9]+)/like', PostLike),
    ('/blogs/([0-9]+)/posts/([0-9]+)/comments/([0-9]+)', CommentUpdate),
    ('/blogs/([0-9]+)/posts/([0-9]+)/comments/([0-9]+)/delete', CommentDelete),

    ('/posts/new', NewPost),
    ('/posts/like', PostLikeList),

], debug=True)
