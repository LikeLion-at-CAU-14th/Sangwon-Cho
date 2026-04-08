from django.urls import path
from posts.views import *

urlpatterns = [
    # path('', hello_world, name = 'hello_world'),
    # path('page', index, name='my-page'),
    # path('<int:id>', get_post_detail)

    path('', post_list, name="post_list"),
    path('<int:post_id>/', post_detail, name = "post_detail"),
    path('<int:post_id>/comment/', comment_list, name = "comment_list")
]