from django.db import models
from django.core.validators import MinValueValidator
from core.models import BaseModel


class Category(BaseModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=350, unique=True)
    description = models.TextField()
    base_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    sku = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
        ]

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True, is_verified=True)
        if reviews.exists():
            return reviews.aggregate(avg=models.Avg('rating'))['avg']
        return None

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()


class ProductImage(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', '-is_primary']

    def __str__(self):
        return f'Image for {self.product.name}'


class CustomizationOption(BaseModel):
    OPTION_TYPES = (
        ('text', 'Text Input'),
        ('textarea', 'Text Area'),
        ('select', 'Dropdown Select'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox (Multiple)'),
        ('color', 'Color Picker'),
        ('file', 'File Upload'),
    )
    name = models.CharField(max_length=200)
    option_type = models.CharField(max_length=10, choices=OPTION_TYPES)
    is_required = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.name


class CustomizationValue(BaseModel):
    MODIFIER_TYPES = (
        ('fixed', 'Fixed Amount'),
        ('percent', 'Percentage'),
    )
    option = models.ForeignKey(CustomizationOption, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=200)
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    modifier_type = models.CharField(max_length=10, choices=MODIFIER_TYPES, default='fixed')
    is_default = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return f'{self.option.name}: {self.value}'


class ProductCustomization(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_customizations')
    option = models.ForeignKey(CustomizationOption, on_delete=models.CASCADE)
    is_required_override = models.BooleanField(null=True, blank=True)
    min_value = models.PositiveIntegerField(null=True, blank=True, help_text='Min selections for checkbox type')
    max_value = models.PositiveIntegerField(null=True, blank=True, help_text='Max selections for checkbox type')

    class Meta:
        unique_together = ('product', 'option')
        ordering = ['option__display_order']

    def __str__(self):
        return f'{self.product.name} - {self.option.name}'

    @property
    def is_required(self):
        if self.is_required_override is not None:
            return self.is_required_override
        return self.option.is_required


class Inventory(BaseModel):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='inventory')
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ['product__name']

    def __str__(self):
        return f'{self.product.name} - Stock: {self.stock_quantity}'

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.low_stock_threshold
