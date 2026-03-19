from rest_framework import serializers
from .models import Product, SupplierProduct, ProductImage, PurchaseOrder, StockLedger, SupplierPayment
from categories.models import Category
from suppliers.models import Supplier
from accounts.fields import ObjectIdField
from accounts.base_serializers import BaseMongoSerializer
from bson import ObjectId
from django.contrib.auth import get_user_model

User = get_user_model()

class ProductImageSerializer(BaseMongoSerializer):
    id = ObjectIdField(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'is_primary')

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None

class SupplierProductSerializer(BaseMongoSerializer):
    id = ObjectIdField(source='pk', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.SerializerMethodField()
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    
    # Aliases for frontend consistency
    available_quantity = serializers.IntegerField(source='available_stock')
    price = serializers.DecimalField(source='supplier_price', max_digits=12, decimal_places=2, required=False)
    gold_weight = serializers.DecimalField(source='weight', max_digits=10, decimal_places=3, required=False)
    
    uploaded_images = serializers.ListField(
        child=serializers.FileField(max_length=10000000, allow_empty_file=False),
        write_only=True,
        required=False
    )

    class Meta:
        model = SupplierProduct
        fields = (
            'id', 'supplier', 'name', 'description', 'category', 'category_name', 
            'metal_type', 'gold_weight', 'price', 'suggested_retail_price', 
            'available_quantity', 'supplier_sku', 'images', 'uploaded_images',
            'purity', 'diamond_clarity', 'status', 'admin_notes', 
            'created_at', 'updated_at'
        )
        read_only_fields = ('supplier', 'created_at', 'updated_at', 'status', 'admin_notes')

    def to_internal_value(self, data):
        # Handle QueryDict (FormData)
        if hasattr(data, 'getlist'):
            internal_data = {}
            for key in data.keys():
                if key == 'uploaded_images':
                    internal_data[key] = data.getlist(key)
                else:
                    internal_data[key] = data.get(key)
            
            # Clean empty strings for specific fields
            for field in ['category', 'gold_weight', 'price', 'suggested_retail_price', 'available_quantity']:
                if field in internal_data and (internal_data[field] == '' or internal_data[field] == 'null' or internal_data[field] == 'undefined'):
                    internal_data[field] = None
            
            return super().to_internal_value(internal_data)
        
        return super().to_internal_value(data)

    def get_category_name(self, obj):
        return obj.category.name if obj.category else "Uncategorized"

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        product = SupplierProduct.objects.create(**validated_data)
        for image in uploaded_images:
            ProductImage.objects.create(supplier_product=product, image=image)
        return product

class ProductSerializer(BaseMongoSerializer):
    id = ObjectIdField(source='pk', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.SerializerMethodField()
    supplier_name = serializers.SerializerMethodField()
    
    # Use simple names for frontend mapping
    price = serializers.DecimalField(source='selling_price', max_digits=12, decimal_places=2)
    available_quantity = serializers.IntegerField(source='stock_quantity')
    is_active = serializers.BooleanField(source='is_enabled', default=True, required=False)
    
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    
    # This handles multiple images during creation/update
    uploaded_images = serializers.ListField(
        child=serializers.FileField(max_length=10000000, allow_empty_file=False),
        write_only=True,
        required=False
    )
    
    # IDs of existing images to keep. If an ID is NOT in this list, it will be deleted.
    keep_images = serializers.ListField(
        child=ObjectIdField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'description', 'price', 'available_quantity', 
            'is_active', 'sku', 'category', 'category_name', 'images', 
            'uploaded_images', 'keep_images', 'metal_type', 'weight',
            'purity', 'diamond_clarity', 'cost_price', 'selling_price',
            'retail_price', 'making_charges', 'gst_percentage',
            'is_featured', 'is_approved', 'created_at', 'updated_at', 'supplier_name'
        )
        read_only_fields = ('slug', 'sku', 'created_at', 'updated_at')

    def to_internal_value(self, data):
        # When using MultiPartParser, data is a QueryDict.
        # DRF's ListField does NOT automatically call getlist() on a QueryDict.
        if hasattr(data, 'getlist'):
            # Create a dictionary to hold the processed values
            internal_data = {}
            
            # Map all keys from QueryDict to internal_data
            for key in data.keys():
                if key == 'uploaded_images':
                    internal_data[key] = data.getlist(key)
                elif key == 'keep_images':
                    # keep_images might be sent as multiple keys or comma separated
                    val = data.getlist(key)
                    if len(val) == 1 and ',' in val[0]:
                        internal_data[key] = [x.strip() for x in val[0].split(',') if x.strip()]
                    else:
                        internal_data[key] = [x for x in val if x]
                else:
                    internal_data[key] = data.get(key)
            
            # Special handling for numeric/related fields that might be empty strings
            for field in ['category', 'supplier', 'weight', 'price', 'available_quantity', 'cost_price', 'selling_price']:
                if field in internal_data and (internal_data[field] == '' or internal_data[field] == 'null' or internal_data[field] == 'undefined'):
                    internal_data[field] = None
                    
            # Boolean fields: Convert "true"/"false" strings to Booleans
            for field in ['is_active', 'is_featured', 'is_approved']:
                if field in internal_data:
                    val = internal_data[field]
                    if isinstance(val, str):
                        internal_data[field] = val.lower() == 'true'

            return super().to_internal_value(internal_data)
        
        return super().to_internal_value(data)


    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role != 'ADMIN':
                representation.pop('cost_price', None)
        else:
            representation.pop('cost_price', None)
        return representation

    def get_category_name(self, obj):
        return obj.category.name if obj.category else "Uncategorized"

    def get_supplier_name(self, obj):
        if obj.supplier:
            return obj.supplier.company_name
        if obj.supplier_user:
            try:
                return obj.supplier_user.supplier_profile.company_name
            except:
                return obj.supplier_user.email
        return "Direct Stock"

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        # We don't need keep_images during create
        validated_data.pop('keep_images', [])
        
        product = Product.objects.create(**validated_data)
        
        for image in uploaded_images:
            ProductImage.objects.create(product=product, image=image)
            
        return product

    def update(self, instance, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        keep_images = validated_data.pop('keep_images', None)
        
        # Update product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Handle existing images deletion
        if keep_images is not None:
            # Delete images that are NOT in the keep_images list
            images_to_delete = instance.images.exclude(id__in=keep_images)
            images_to_delete.delete() # This will trigger post_delete signal
            
        # Add new images if any
        for image in uploaded_images:
            ProductImage.objects.create(product=instance, image=image)
            
        return instance

class CategorySerializer(BaseMongoSerializer):
    id = ObjectIdField(read_only=True)
    subcategories = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'parent', 'description', 'image', 'subcategories')

    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return CategorySerializer(obj.subcategories.all(), many=True).data
        return []


class PurchaseOrderSerializer(BaseMongoSerializer):
    id = ObjectIdField(source='pk', read_only=True)
    supplier = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='SUPPLIER'), required=False)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(), required=False)
    supplier_email = serializers.EmailField(source='supplier.email', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payment_status = serializers.CharField(read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = (
            'id', 'supplier', 'supplier_email', 'product', 'product_name', 'product_sku', 
            'quantity', 'unit_cost_price', 'total_cost', 'status', 'amount_paid', 
            'remaining_amount', 'payment_status', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class SupplierPaymentSerializer(BaseMongoSerializer):
    id = ObjectIdField(source='pk', read_only=True)
    purchase_order_id = serializers.PrimaryKeyRelatedField(
        queryset=PurchaseOrder.objects.all(), source='purchase_order', write_only=True
    )
    
    class Meta:
        model = SupplierPayment
        fields = ('id', 'purchase_order', 'purchase_order_id', 'amount_paid', 'payment_method', 'transaction_id', 'payment_date', 'notes')
        read_only_fields = ('id', 'payment_date', 'purchase_order')


class ProductDetailSerializer(BaseMongoSerializer):
    id = ObjectIdField(source='pk', read_only=True)
    category = ObjectIdField(required=False, allow_null=True)
    supplier_user = ObjectIdField(required=False, allow_null=True)
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.SerializerMethodField()
    supplier_email = serializers.SerializerMethodField()
    margin = serializers.SerializerMethodField()
    margin_percentage = serializers.SerializerMethodField()
    price = serializers.DecimalField(source='selling_price', max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'description', 'price', 'cost_price', 'selling_price', 
            'retail_price', 'making_charges', 'gst_percentage',
            'margin', 'margin_percentage', 'stock_quantity', 'sku', 'category', 
            'category_name', 'images', 'metal_type', 'weight', 'purity', 'diamond_clarity', 
            'is_featured', 'is_approved', 'supplier_user', 'supplier_email',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'slug', 'sku', 'created_at', 'updated_at')
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role != 'ADMIN':
                representation.pop('cost_price', None)
        else:
            representation.pop('cost_price', None)
        return representation

    def get_category_name(self, obj):
        return obj.category.name if obj.category else "Uncategorized"
    
    def get_supplier_email(self, obj):
        return obj.supplier_user.email if obj.supplier_user else None
    
    def get_margin(self, obj):
        return obj.margin
    
    def get_margin_percentage(self, obj):
        return obj.margin_percentage

class StockLedgerSerializer(BaseMongoSerializer):
    id = ObjectIdField(source='pk', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    entry_type_display = serializers.CharField(source='get_entry_type_display', read_only=True)

    class Meta:
        model = StockLedger
        fields = '__all__'
