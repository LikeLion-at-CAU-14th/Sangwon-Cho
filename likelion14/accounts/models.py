from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

    # 모델 함수
    @staticmethod
    def get_user_by_username(username):
        try:
            return User.objects.get(username=username)
        except Exception:
            return None
        
    # 추가       
    @staticmethod
    def get_user_by_email(email):
        try:
            return User.objects.get(email=email)
        except Exception:
            return None