from django.contrib import admin
from django.urls import path, include
from posts.views import *

urlpatterns = [
    # path('', hello_world, name = 'hello_world'),
    # path('page', index, name='my-page'),
    # path('<int:id>', get_post_detail)

    # path('', post_list, name="post_list"),
    # path('<int:post_id>/', post_detail, name = "post_detail"),
    # path('<int:post_id>/comment/', comment_list, name = "comment_list")

    path('', PostList.as_view()), # post 전체 조회
    path('<int:post_id>/', PostDetail.as_view()), # post 개별 조회
    # path('<int:id>/', get_post_detail),
    path('<int:post_id>/comment/', CommentList.as_view()), # comment 전체 조회 및 생성
    path('<int:post_id>/comment/<int:comment_id>/', CommentDetail.as_view()), # comment 개별 삭제
    path('upload/', ImageUploadView.as_view(), name='image-upload')

]