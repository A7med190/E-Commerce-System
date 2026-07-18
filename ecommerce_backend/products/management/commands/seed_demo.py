from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import (
    Category, Product, Inventory, CustomizationOption, CustomizationValue,
    ProductCustomization,
)


class Command(BaseCommand):
    help = 'Seed demo data: categories, customizable products, inventory.'

    def handle(self, *args, **options):
        if Category.objects.exists() or Product.objects.exists():
            self.stdout.write(self.style.WARNING('Data already exists. Skipping seed.'))
            return

        # Categories
        cats = {
            'apparel': self._cat('Apparel', 'Custom t-shirts, hoodies and more.'),
            'accessories': self._cat('Accessories', 'Mugs, phone cases, bags.'),
            'home': self._cat('Home & Living', 'Posters, pillows, decor.'),
        }
        cats['tshirts'] = self._cat('T-Shirts', 'Custom printed tees.', parent=cats['apparel'])
        cats['hoodies'] = self._cat('Hoodies', 'Cozy custom hoodies.', parent=cats['apparel'])
        cats['mugs'] = self._cat('Mugs', 'Personalized drinkware.', parent=cats['accessories'])

        # Reusable options
        size = self._option('Size', 'select', True, order=1)
        self._value(size, 'Small', 0, 'fixed', is_default=True, order=1)
        self._value(size, 'Medium', 0, 'fixed', order=2)
        self._value(size, 'Large', 0, 'fixed', order=3)
        self._value(size, 'XL', 2.00, 'fixed', order=4)

        color = self._option('Color', 'color', True, order=2)
        self._value(color, 'Black', 0, 'fixed', is_default=True, order=1)
        self._value(color, 'White', 0, 'fixed', order=2)
        self._value(color, 'Navy', 0, 'fixed', order=3)
        self._value(color, 'Red', 0, 'fixed', order=4)

        material = self._option('Material', 'select', False, order=3)
        self._value(material, 'Cotton', 0, 'fixed', is_default=True, order=1)
        self._value(material, 'Organic Cotton', 4.00, 'fixed', order=2)
        self._value(material, 'Bamboo Blend', 6.00, 'fixed', order=3)

        print_style = self._option('Print Style', 'select', False, order=4)
        self._value(print_style, 'Front Print', 0, 'fixed', is_default=True, order=1)
        self._value(print_style, 'Front & Back', 5.00, 'fixed', order=2)
        self._value(print_style, 'All Over Print', 12.00, 'fixed', order=3)

        add_name = self._option('Add Your Name', 'text', False, order=5)
        self._value(add_name, 'No name', 0, 'fixed', is_default=True, order=1)
        self._value(add_name, 'Add name (+$3)', 3.00, 'fixed', order=2)

        gift_wrap = self._option('Gift Wrapping', 'checkbox', False, order=6)
        self._value(gift_wrap, 'Premium Wrap', 4.50, 'fixed', order=1)
        self._value(gift_wrap, 'Gift Card', 1.50, 'fixed', order=2)

        mug_size = self._option('Mug Size', 'select', True, order=1)
        self._value(mug_size, '11 oz', 0, 'fixed', is_default=True, order=1)
        self._value(mug_size, '15 oz', 3.00, 'fixed', order=2)

        mug_color = self._option('Mug Color', 'color', True, order=2)
        self._value(mug_color, 'White', 0, 'fixed', is_default=True, order=1)
        self._value(mug_color, 'Black', 0, 'fixed', order=2)

        # Products
        self._product(
            'Classic Custom Tee', cats['tshirts'], 24.99,
            'A soft, breathable cotton tee you can make your own with size, color, material and print options.',
            featured=True, options=[size, color, material, print_style, add_name],
        )
        self._product(
            'Premium Hoodie', cats['hoodies'], 49.99,
            'Warm fleece-lined hoodie with customizable size, color and print placement.',
            featured=True, options=[size, color, print_style, gift_wrap],
        )
        self._product(
            'Everyday Cotton Tee', cats['tshirts'], 19.99,
            'Affordable everyday tee with size and color choices.',
            options=[size, color],
        )
        self._product(
            'Personalized Coffee Mug', cats['mugs'], 14.99,
            'Start your morning with a custom mug. Choose size, color and add gift wrapping.',
            featured=True, options=[mug_size, mug_color, gift_wrap],
        )
        self._product(
            'Statement Hoodie', cats['hoodies'], 54.99,
            'Bold hoodie with all-over print option for maximum style.',
            options=[size, color, print_style, add_name],
        )

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))

    def _cat(self, name, desc, parent=None):
        return Category.objects.create(
            name=name, slug=slugify(name), description=desc, parent=parent
        )

    def _option(self, name, otype, required, order):
        return CustomizationOption.objects.create(
            name=name, option_type=otype, is_required=required, display_order=order
        )

    def _value(self, option, value, modifier, mtype, is_default=False, order=1):
        return CustomizationValue.objects.create(
            option=option, value=value, price_modifier=modifier,
            modifier_type=mtype, is_default=is_default, display_order=order,
        )

    def _product(self, name, category, price, desc, featured=False, options=None):
        product = Product.objects.create(
            name=name, slug=slugify(name), description=desc,
            base_price=price, sku=slugify(name)[:20].upper(), category=category,
            is_active=True, is_featured=featured,
        )
        Inventory.objects.create(product=product, stock_quantity=50, low_stock_threshold=10)
        for opt in (options or []):
            ProductCustomization.objects.create(product=product, option=opt)
        return product
