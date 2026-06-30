from django.shortcuts import render
from django.http import JsonResponse # 추가 
from django.shortcuts import get_object_or_404 # 추가
from django.views.decorators.http import require_http_methods
from .models import *
import json

### DRF 관련 import - APIView 사용
from .serializers import PostSerializer, CommentSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from accounts.models import User

from rest_framework.permissions import IsAuthenticatedOrReadOnly # jwt 세션

from config.permissions import CustomPermissionOwnerOrReadOnly, CustomPermissionTime

from django.core.files.storage import default_storage  
from .serializers import ImageSerializer
from django.conf import settings
import boto3
import uuid

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi




class ImageUploadView(APIView):
    @swagger_auto_schema(
        operation_summary="이미지 업로드",
        operation_description="이미지 파일을 S3에 업로드합니다.",
        manual_parameters=[
            openapi.Parameter(
                name="image",
                in_=openapi.IN_FORM,
                description="업로드할 이미지 파일",
                type=openapi.TYPE_FILE,
                required=True,
            )
        ],
        consumes=["multipart/form-data"],
        responses={201: ImageSerializer, 400: "잘못된 요청", 500: "S3 업로드 실패"},
    )
    def post(self, request):
        if 'image' not in request.FILES:
            return Response({"error": "No image file"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES['image']

        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )

        # S3에 파일 저장
        file_path = f"uploads/{uuid.uuid4()}_{image_file.name}"
        # S3에 파일 업로드
        try:
            s3_client.put_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=file_path,
                Body=image_file.read(),
                ContentType=image_file.content_type,
            )
        except Exception as e:
            return Response({"error": f"S3 Upload Failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 업로드된 파일의 URL 생성
        image_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{file_path}"
        
        # DB에 저장
        image_instance = Image.objects.create(image_url=image_url)
        serializer = ImageSerializer(image_instance)


        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
class PostList(APIView):
    permission_classes = [CustomPermissionTime, IsAuthenticatedOrReadOnly]
    @swagger_auto_schema(
            operation_summary="게시글 생성",
            operation_description="새로운 게시글을 생성합니다.",
            request_body=PostSerializer,  # 요청 데이터의 스키마 정의
            responses={201: PostSerializer, 400: "잘못된 요청"},  # 응답 데이터의 스키마 정의
    )
    def post(self, request, format=None):
        # 생성이라 유효성 검사 필요
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(writer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="게시글 목록 조회",
        operation_description="모든 게시글을 조회합니다.",
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request, format=None):
        posts = Post.objects.all()
        serializer = PostSerializer(posts, many=True)
        return Response(serializer.data)


class PostDetail(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, CustomPermissionTime, CustomPermissionOwnerOrReadOnly]
    @swagger_auto_schema(
            operation_summary="게시글 조회",
            operation_description="게시글을 조회합니다.",
            responses={200: PostSerializer},
    )
    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        serializer = PostSerializer(post)
        return Response(serializer.data)

    @swagger_auto_schema(
            operation_summary="게시글 수정",
            operation_description="기존 게시글을 수정합니다.",
            request_body=PostSerializer,  # 요청 데이터의 스키마 정의
            responses={200: PostSerializer, 400: "잘못된 요청"},  # 응답 데이터의 스키마 정의
    )
    def put(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        self.check_object_permissions(request, post)
        serializer = PostSerializer(post, data=request.data)
        if serializer.is_valid(): # update이니까 유효성 검사 필요
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)   
    
    @swagger_auto_schema(
            operation_summary="게시글 삭제",
            operation_description="기존 게시글을 삭제합니다.",
            responses={200: openapi.Response(description="게시글이 성공적으로 삭제되었습니다.")},
    )
    def delete(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        self.check_object_permissions(request, post)
        post.delete()
        return Response(
            {
                "message": "게시글이 성공적으로 삭제되었습니다.",
                "post_id": post_id
            },
            status=status.HTTP_200_OK
        )
    
class CommentList(APIView):
    permission_classes = [CustomPermissionTime, IsAuthenticatedOrReadOnly]
    
    @swagger_auto_schema(
            operation_summary="댓글 조회",
            operation_description="댓글을 조회합니다.",
            responses={200: CommentSerializer(many=True)},
    )
    def get(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        comments = post.comment.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
            operation_summary="댓글 작성",
            operation_description="새로운 댓글을 작성합니다.",
            request_body=CommentSerializer,  # 요청 데이터의 스키마 정의
            responses={201: CommentSerializer, 400: "잘못된 요청"},  # 응답 데이터의 스키마 정의
    )
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)
        # request.data에 post_id를 추가하여 serializer에 전달
        data = request.data.copy()
        data['post'] = post_id
        
        serializer = CommentSerializer(data=data)
        if serializer.is_valid():
            serializer.save(writer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDetail(APIView):
    permission_classes = [CustomPermissionTime, IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
            operation_summary="댓글 삭제",
            operation_description="기존 댓글을 삭제합니다.",
            responses={200: openapi.Response(description="댓글이 성공적으로 삭제되었습니다.")},
    )
    def delete(self, request, post_id, comment_id):
        post = get_object_or_404(Post, id=post_id)
        comment = get_object_or_404(Comment, id=comment_id, post=post)
        comment.delete()
        return Response(
            {
                "message": "댓글이 성공적으로 삭제되었습니다.",
                "comment_id": comment_id
            },
            status=status.HTTP_200_OK
        )
    

# # 게시글을 Post(Create), Get(Read) 하는 뷰 로직
# @require_http_methods(["POST", "GET"])   #함수 데코레이터, 특정 http method 만 허용합니다
# def post_list(request):

#     if request.method == "POST":

#         # request.body의 byte -> 문자열 -> python 딕셔너리
#         body = json.loads(request.body.decode('utf-8'))

#         # 프론트에게서 user id를 넘겨받는다고 가정.
# 				# 외래키 필드의 경우, 객체 자체를 전달해줘야하기 때문에
#         # id를 기반으로 user 객체를 조회해서 가져옵니다 !
#         user_id = body.get('user')
#         user = get_object_or_404(User, pk=user_id)

#         # 새로운 데이터를 DB에 생성
#         new_post = Post.objects.create(
#             title = body['title'],
#             content = body['content'],
#             status = body['status'],
#             writer = user
#         )

#         # Json 형태 반환 데이터 생성
#         new_post_json = {
#             "id" : new_post.id,
#             "title" : new_post.title,
#             "content" : new_post.content,
#             "status" : new_post.status,
#             "writer" : new_post.writer.username
#         }

#         return JsonResponse({
#             'status' : 200,
#             'message' : '게시글 생성 성공',
#             'data' : new_post_json
#         })
    
#     # 게시글 전체 조회
#     if request.method == "GET":
#         post_all = Post.objects.order_by('-created_at')

#         category_name = request.GET.get('category', None)
#         if category_name:
#             post_all = post_all.filter(category__name=category_name)

#         # 각 데이터를 Json 형식으로 변환하여 리스트에 저장 (여러개의 게시글 내용을 담을 거라 리스트를 이용합니다)
#         post_all_json = []

#         for post in post_all:
#             post_json = {
#                 "id" : post.id,
#                 "title" : post.title,
#                 "content" : post.content,
#                 "status" : post.status,
#                 "writer" : post.writer.username
#             }
#             post_all_json.append(post_json)

#         return JsonResponse({
#             'status' : 200,
#             'message' : '게시글 목록 조회 성공',
#             'data' : post_all_json
#         })

# # 게시글 단일조회(GET), 수정(PATCH) 로직
# @require_http_methods(["GET","PATCH", "DELETE"])
# def post_detail(request, post_id):
    
#     if request.method == "GET":
#         post = get_object_or_404(Post, pk=post_id) # post_id 에 해당하는 Post 데이터 가져오기
    
#         post_json_detail = {
#             "id" : post.id,
#             "title" : post.title,
#             "content" : post.content,
#             "status" : post.status,
#             "writer" : post.writer.username
#         }
#         return JsonResponse({
#             "status" : 200,
#             'message' : '게시글 단일 조회 성공',
#             "data": post_json_detail})
    
#     if request.method == "PATCH":
#         body = json.loads(request.body.decode('utf-8'))

#         post_update = get_object_or_404(Post, pk=post_id)

#         if 'title' in body:
#             post_update.title = body['title']
#         if 'content' in body:
#             post_update.content = body['content']
#         if 'status' in body:
#             post_update.status = body['status']
        
#         post_update.save()

#         post_update_json = {
#             "id" : post_update.id,
#             "title" : post_update.title,
#             "content" : post_update.content,
#             "status" : post_update.status,
#             "writer" : post_update.writer.username
#         }

#         return JsonResponse({
#             'status': 200,
#             'message' : '게시글 수정 성공',
#             'data' : post_update_json
#         })
    
#     if request.method == "DELETE":
#         post_delete = get_object_or_404(Post, pk=post_id)
#         post_delete.delete()

#         return JsonResponse({
#             'status' : 200,
#             'message' : '게시글 삭제 성공',
#             'data' : None
#         })

# @require_http_methods(["GET", "POST"])
# def comment_list(request, post_id):
#     if request.method == "GET":
#         post = get_object_or_404(Post, pk=post_id)
#         comment_all = post.comment.all().order_by('-created_at')

#         comment_all_json = []

#         for comment in comment_all:
#             comment_json = {
#                 "id" : comment.id,
#                 "content" : comment.content
#             }
#             comment_all_json.append(comment_json)

#         return JsonResponse({
#             'status' : 200,
#             'message' : '댓글 목록 조회 성공',
#             'data' : comment_all_json
#         })
    
#     if request.method == "POST":
#         body = json.loads(request.body.decode('utf-8'))

#         user_id = body.get('user')
#         user = get_object_or_404(User, pk=user_id)

#         post = get_object_or_404(Post, pk=post_id)

#         new_comment = Comment.objects.create(
#             content = body['content'],
#             post = post,
#             writer = user
#         )

#         new_comment_json = {
#             "id" : new_comment.id,
#             "content" : new_comment.content
#         }

#         return JsonResponse({
#             'status' : 200,
#             'message' : '댓글 생성 성공',
#             'data' : new_comment_json
#         })


# # Create your views here.

# def hello_world(request):
#     if request.method == "GET":
#         return JsonResponse({
#             'status' : 200,
#             'data' : "Hello likelion-14th!"
#         })
    
# def index(request):
#     return render(request, 'index.html')