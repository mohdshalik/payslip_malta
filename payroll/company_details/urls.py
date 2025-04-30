from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet,DepartmentViewSet,UserViewSet

router = DefaultRouter()

router.register(r'User', UserViewSet)
router.register(r'company', CompanyViewSet)
router.register(r'department', DepartmentViewSet)




urlpatterns = [
    path('api/', include(router.urls)),
]