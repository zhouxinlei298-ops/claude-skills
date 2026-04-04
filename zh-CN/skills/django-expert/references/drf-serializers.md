# DRF 序列化器

## ModelSerializer

```python
from rest_framework import serializers

class ProductSerializer(serializers.ModelSerializer):
    # Read-only computed field
    category_name = serializers.CharField(source='category.name', read_only=True)

    # Write-only for input
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    # Nested read-only
    created_by = UserSerializer(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'stock',
            'category_name', 'category_id', 'created_by', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']
```

## 字段级验证

```python
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['name', 'price', 'stock']

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative")
        return value

    def validate_name(self, value):
        if Product.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Product name already exists")
        return value
```

## 对象级验证

```python
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['product', 'quantity', 'shipping_address']

    def validate(self, attrs):
        product = attrs['product']
        quantity = attrs['quantity']

        if quantity > product.stock:
            raise serializers.ValidationError({
                'quantity': f'Only {product.stock} items available'
            })

        if not attrs.get('shipping_address') and quantity > 5:
            raise serializers.ValidationError(
                "Shipping address required for large orders"
            )

        return attrs
```

## 嵌套序列化器

```python
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'total', 'created_at']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)

        return instance
```

## SerializerMethodField

```python
class ProductSerializer(serializers.ModelSerializer):
    discount_price = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['name', 'price', 'discount_price', 'is_available']

    def get_discount_price(self, obj) -> float:
        discount = self.context.get('discount', 0)
        return obj.price * (1 - discount / 100)

    def get_is_available(self, obj) -> bool:
        return obj.stock > 0 and obj.is_active
```

## 快速参考

| 字段类型 | 用途 |
|----------|------|
| `CharField(source=...)` | 从关联对象计算 |
| `PrimaryKeyRelatedField` | 外键输入 |
| `SerializerMethodField` | 自定义计算 |
| `嵌套序列化器` | 关联对象 |

| 方法 | 用途 |
|------|------|
| `validate_<field>()` | 单字段验证 |
| `validate()` | 跨字段验证 |
| `create()` | 自定义创建逻辑 |
| `update()` | 自定义更新逻辑 |
| `to_representation()` | 自定义输出 |
