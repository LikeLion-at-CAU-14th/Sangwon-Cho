from rest_framework.permissions import BasePermission
from django.utils import timezone
from zoneinfo import ZoneInfo

# 특정 시간대(밤 10시~아침 7시)에는 게시판의 모든 API 요청 제한   
class CustomPermissionTime(BasePermission):
    def has_permission(self, request, view):
        now = timezone.localtime(timezone.now(), ZoneInfo("Asia/Seoul"))
        if 7 <= now.hour < 22:
            return True
        return False
    
# 이외의 시간대에는 게시판 이용이 가능하며, 게시글의 주인만 수정, 삭제가 가능하고 이외의 사용자는 읽기 권한만 가짐
class CustomPermissionOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.writer == request.user
