### Model Serializer case

from rest_framework import serializers
from .models import Post, Comment
from .models import Image
from config.custom_api_exceptions import PostConflictException, ValidationErrorException


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = "__all__"

        
class PostSerializer(serializers.ModelSerializer):

  class Meta:
    model = Post    # serializer가 어떤 모델을 기반으로 만들어지는지 >> post
    fields = "__all__"  # 모델에서 어떤 필드를 가져올지 >> 전체 필드
    read_only_fields = ("writer",)

  def validate(self, data):
    title = data.get('title')
    if title and Post.objects.filter(title=title).exists():
      raise PostConflictException(detail=f"A post with title: '{title}' already exists.")
    
    return data
  
  def isnull(self, data):
    if data is None:
      raise ValidationErrorException(detail="Data cannot be null.")
    
    return data


class CommentSerializer(serializers.ModelSerializer):

  class Meta:
    model = Comment
    fields = "__all__"
    read_only_fields = ("writer",)

  def validate_content(self, value):
    if len(value.strip()) < 15:
      raise ValidationErrorException(detail="댓글은 최소 15자 이상 작성해주세요.")

    return value
