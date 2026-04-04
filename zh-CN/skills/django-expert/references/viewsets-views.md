# ViewSet 与视图

## ModelViewSet

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'created_by')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['price', 'created_at']
    lookup_field = 'slug'

    def get_queryset(self):
        qs = super().get_queryset()
        if self.action == 'list':
            return qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def purchase(self, request, slug=None):
        product = self.get_object()
        quantity = request.data.get('quantity', 1)

        if product.stock < quantity:
            return Response(
                {'error': 'Insufficient stock'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.stock -= quantity
        product.save()
        return Response({'message': 'Purchase successful'})

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured = self.get_queryset().filter(is_featured=True)[:10]
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)
```

## Django 5.0 异步视图

```python
from django.http import JsonResponse
from asgiref.sync import sync_to_async

# Async function-based view
async def user_list(request):
    users = await sync_to_async(list)(
        User.objects.all()[:100]
    )
    return JsonResponse({'users': [u.to_dict() for u in users]})

# Async class-based view
from django.views import View

class AsyncProductView(View):
    async def get(self, request, product_id):
        product = await sync_to_async(
            Product.objects.select_related('category').get
        )(pk=product_id)
        return JsonResponse({
            'id': product.id,
            'name': product.name,
            'category': product.category.name,
        })
```

## 通用视图

```python
from rest_framework import generics

class ProductListCreate(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    lookup_field = 'slug'
```

## URL 配置

```python
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')

urlpatterns = [
    path('api/', include(router.urls)),
]

# Generated URLs:
# GET/POST    /api/products/
# GET/PUT/DELETE /api/products/{slug}/
# POST        /api/products/{slug}/purchase/
# GET         /api/products/featured/
```

## 分页

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# Custom pagination
from rest_framework.pagination import PageNumberPagination

class LargeResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000

class ProductViewSet(viewsets.ModelViewSet):
    pagination_class = LargeResultsSetPagination
```

## 快速参考

| ViewSet 方法 | HTTP | 操作 |
|--------------|------|------|
| `list()` | GET | 列表查询 |
| `create()` | POST | 新建 |
| `retrieve()` | GET | 获取单个 |
| `update()` | PUT | 完整更新 |
| `partial_update()` | PATCH | 部分更新 |
| `destroy()` | DELETE | 删除 |

| 钩子 | 用途 |
|------|------|
| `get_queryset()` | 过滤查询集 |
| `get_serializer_class()` | 动态序列化器 |
| `perform_create()` | 保存前逻辑 |
| `@action()` | 自定义端点 |
