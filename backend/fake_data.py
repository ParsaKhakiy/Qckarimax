# populate_fake_data.py
import os
import random
import decimal
from datetime import timedelta, datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.dev')
import django
django.setup()

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from faker import Faker
from Sales.models import SalesExpert, OrderHistoryCreator
from product.models import Product, Category, ProductionLine, ProductionTask, Requirements, Operator, RequirementsProducts
from order.models import Order
from django.db import transaction

fake = Faker('fa_IR')

User = get_user_model()

def create_categories():
    """ایجاد دسته‌بندی‌های محصول"""
    categories = [
        'لوازم الکترونیکی', 'لوازم خانگی', 'پوشاک', 'کتاب', 'مواد غذایی',
        'ابزار', 'لوازم ورزشی', 'زیبایی و سلامت', 'اسباب بازی', 'ماشین‌آلات'
    ]
    
    created_categories = []
    for cat_name in categories:
        category, created = Category.objects.get_or_create(
            title=cat_name,
            defaults={'slug': slugify(cat_name, allow_unicode=True)}
        )
        created_categories.append(category)
        print(f'دسته‌بندی ایجاد شد: {category}')
    
    return created_categories

def create_products_and_requirements(num_products=50):
    """ایجاد محصولات و نیازمندی‌های مربوطه"""
    categories = Category.objects.all()
    
    # ایجاد برخی اپراتورها
    operators = []
    for _ in range(10):
        operator = Operator.objects.create(
            name=fake.first_name(),
            family=fake.last_name(),
            description=fake.text(max_nb_chars=200),
            slug=slugify(f"{fake.first_name()} {fake.last_name()}", allow_unicode=True)
        )
        operators.append(operator)
    
    # ایجاد برخی نیازمندی‌ها
    requirements_list = []
    req_names = ['تایید کیفیت', 'بسته‌بندی ویژه', 'گواهی سلامت', 'نصب و راه‌اندازی', 'ضمانت اضافه']
    for req_name in req_names:
        req, created = Requirements.objects.get_or_create(
            name=req_name,
            defaults={
                'description': fake.text(max_nb_chars=150),
                'slug': slugify(req_name, allow_unicode=True)
            }
        )
        requirements_list.append(req)
    
    # ایجاد خطوط تولید
    production_lines = []
    line_names = ['خط تولید A', 'خط تولید B', 'خط مونتاژ', 'خط کنترل کیفیت', 'خط بسته‌بندی']
    for line_name in line_names:
        line, created = ProductionLine.objects.get_or_create(
            name=line_name,
            defaults={
                'location': fake.city(),
                'capacity': random.randint(3, 10)
            }
        )
        production_lines.append(line)
    
    # ایجاد محصولات
    products = []
    for i in range(num_products):
        category = random.choice(categories)
        product_name = fake.word().capitalize() + ' ' + fake.word().capitalize()
        
        product = Product.objects.create(
            name=product_name,
            slug=slugify(product_name, allow_unicode=True) + f"-{i}",
            description=fake.paragraph(nb_sentences=3),
            category=category,
            price=decimal.Decimal(random.randrange(10000, 1000000, 1000)),
            discount_price=decimal.Decimal(random.randrange(5000, 500000, 1000)) if random.random() > 0.7 else None,
            stock=random.randint(0, 100),
            is_active=random.choice([True, True, True, False])  # 75% فعال
        )
        products.append(product)
        
        # برای بعضی محصولات، نیازمندی‌های تولید ایجاد کن
        if random.random() > 0.5:  # 50% شانس
            req_product = RequirementsProducts.objects.create(
                name=f"نیازمندی‌های {product.name}",
                slug=slugify(f"requirements-{product.slug}", allow_unicode=True),
                description=fake.text(max_nb_chars=200),
                product=product
            )
            
            # اضافه کردن نیازمندی‌های تصادفی
            selected_reqs = random.sample(requirements_list, k=random.randint(1, 3))
            req_product.requirements.set(selected_reqs)
            
            # اضافه کردن خطوط تولید
            selected_lines = random.sample(production_lines, k=random.randint(1, 2))
            req_product.product_timeline.set(selected_lines)
            
            # اضافه کردن اپراتورها
            selected_ops = random.sample(operators, k=random.randint(2, 4))
            req_product.orpertors.set(selected_ops)
    
    print(f'{len(products)} محصول ایجاد شد')
    return products

def create_fake_users_and_sales_experts(num_users=15):
    """ایجاد کاربران و پروفایل فروش آن‌ها"""
    users = []
    sales_experts = []
    
    # ایجاد سوپریوزر برای تست
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@example.com',
            'first_name': 'مدیر',
            'last_name': 'سیستم',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        users.append(admin_user)
        print('کاربر ادمین ایجاد شد')
    
    for i in range(num_users):
        username = fake.user_name() + str(i)
        email = fake.email()
        
        # چک کن که کاربر تکراری نباشه
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                password='testpass123'
            )
            users.append(user)
            
            # فقط 30% کاربران رو کارشناس فروش کن
            if random.random() < 0.3 and len(sales_experts) < 8:  # حداکثر 8 کارشناس فروش
                sales_expert = SalesExpert.objects.create(
                    user=user,
                    employee_code=fake.unique.bothify('EMP-######'),
                    branch=random.choice([
                        'شعبه مرکزی تهران', 
                        'شعبه اصفهان', 
                        'شعبه شیراز', 
                        'واحد فروش آنلاین',
                        'شعبه مشهد'
                    ]),
                    total_sales_amount=decimal.Decimal(random.randrange(0, 50000000, 1000)),
                    total_sales_product_amount=decimal.Decimal(random.randrange(0, 10000, 100)),
                    mount_sale_amount=decimal.Decimal(random.randrange(0, 10000000, 1000)),
                    product_added=random.randint(0, 50),
                    customer_satisfaction=decimal.Decimal(random.randrange(70, 100))  # رضایت 70-100%
                )
                sales_experts.append(sales_expert)
                print(f'کارشناس فروش ایجاد شد: {sales_expert}')
    
    return users, sales_experts

def create_fake_orders(sales_experts, products, num_orders=100):
    """ایجاد سفارشات فیک"""
    if not sales_experts:
        print("هیچ کارشناس فروشی وجود ندارد!")
        return []
    
    orders = []
    status_choices = ['pending', 'paid', 'shipped', 'canceled']
    status_weights = [0.2, 0.5, 0.2, 0.1]  # احتمالات وضعیت‌ها
    
    for i in range(num_orders):
        saler = random.choice(sales_experts)
        product = random.choice(products)
        status = random.choices(status_choices, weights=status_weights)[0]
        
        # تاریخ سفارش رو تصادفی در 90 روز گذشته بساز
        order_date = fake.date_time_between(start_date='-90d', end_date='now')
        
        order = Order.objects.create(
            saler=saler,
            name=f"سفارش {fake.bothify(text='ORD-#####')}",
            description=fake.paragraph(nb_sentences=2),
            customer_name=fake.first_name(),
            customer_family=fake.last_name(),
            address=fake.address(),
            postal_code=fake.bothify(text='##########'),
            city=fake.city(),
            status=status,
            total_price=decimal.Decimal(random.randrange(100000, 5000000, 1000)),
            product=product,
            tracking_code=fake.bothify(text='TRK-##########') if status in ['shipped', 'paid'] else None,
            created_at=order_date,
            updated_at=order_date + timedelta(days=random.randint(0, 7))
        )
        orders.append(order)
        
        # آمار فروش کارشناس رو به‌روز کن
        if status != 'canceled':
            saler.total_sales_amount += order.total_price
            saler.mount_sale_amount += order.total_price
            if random.random() > 0.3:  # 70% شانس
                saler.product_added += 1
            saler.save()
        
        # بعضی سفارش‌ها رو به فرآیند تولید اضافه کن
        if status in ['paid', 'shipped'] and random.random() > 0.5:
            create_production_task_for_order(order)
    
    print(f'{len(orders)} سفارش ایجاد شد')
    return orders

def create_production_task_for_order(order):
    """ایجاد تسک تولید برای سفارش"""
    production_lines = ProductionLine.objects.filter(is_active=True)
    if not production_lines.exists():
        return
    
    production_line = random.choice(list(production_lines))
    
    # چک کن خط تولید ظرفیت آزاد داره
    if production_line.has_free_capacity:
        task_statuses = ['waiting', 'processing', 'qc_pending', 'completed']
        status_weights = [0.3, 0.3, 0.2, 0.2]
        
        task = ProductionTask.objects.create(
            order=order,
            production_line=production_line,
            status=random.choices(task_statuses, weights=status_weights)[0],
            timeline=[
                {
                    'status': 'created',
                    'timestamp': datetime.now().isoformat(),
                    'note': 'تسک تولید ایجاد شد'
                }
            ]
        )
        
        if task.status in ['processing', 'qc_pending', 'completed']:
            task.start_date = fake.date_time_between(
                start_date=order.created_at, 
                end_date='now'
            )
        
        if task.status == 'completed':
            task.end_date = task.start_date + timedelta(days=random.randint(1, 7)) if task.start_date else None
        
        task.save()
        print(f'تسک تولید برای سفارش {order.id} ایجاد شد')

def create_order_histories(sales_experts, orders):
    """ایجاد تاریخچه سفارش برای کارشناسان فروش"""
    for expert in sales_experts:
        # سفارشات این کارشناس رو پیدا کن
        expert_orders = [order for order in orders if order.saler == expert]
        
        if expert_orders:
            # از get_or_create استفاده می‌کنیم
            history, created = OrderHistoryCreator.objects.get_or_create(saleser=expert)
            
            # فقط سفارشات پرداخت شده یا ارسال شده رو اضافه کن
            valid_orders = [order for order in expert_orders 
                          if order.status in ['paid', 'shipped']]
            
            if valid_orders:
                history.orders.add(*valid_orders)
                print(f'تاریخچه برای {expert} ایجاد شد: {len(valid_orders)} سفارش معتبر')

def run():
    """اجرای اصلی تولید داده‌های فیک"""
    print("=" * 50)
    print("شروع تولید داده‌های فیک...")
    print("=" * 50)
    
    # پاک کردن دیتای قدیمی (اختیاری - مراقب باش!)
    # User.objects.filter(is_superuser=False).delete()
    
    try:
        with transaction.atomic():
            # مرحله 1: ایجاد دسته‌بندی‌ها
            print("\n1. ایجاد دسته‌بندی‌ها...")
            create_categories()
            
            # مرحله 2: ایجاد محصولات و نیازمندی‌ها
            print("\n2. ایجاد محصولات و نیازمندی‌های تولید...")
            create_products_and_requirements(30)  # 30 محصول
            
            # مرحله 3: ایجاد کاربران و کارشناسان فروش
            print("\n3. ایجاد کاربران و کارشناسان فروش...")
            users, sales_experts = create_fake_users_and_sales_experts(20)  # 20 کاربر
            
            # مرحله 4: ایجاد سفارشات
            print("\n4. ایجاد سفارشات...")
            orders = create_fake_orders(sales_experts, list(Product.objects.all()[:50]), 80)  # 80 سفارش
            
            # مرحله 5: ایجاد تاریخچه سفارشات
            print("\n5. ایجاد تاریخچه سفارشات...")
            create_order_histories(sales_experts, orders)
            
            # مرحله 6: آمار نهایی
            print("\n6. آمار نهایی تولید داده:")
            print(f"   - کاربران: {User.objects.count()}")
            print(f"   - کارشناسان فروش: {SalesExpert.objects.count()}")
            print(f"   - محصولات: {Product.objects.count()}")
            print(f"   - سفارشات: {Order.objects.count()}")
            print(f"   - تاریخچه‌های سفارش: {OrderHistoryCreator.objects.count()}")
            print(f"   - تسک‌های تولید: {ProductionTask.objects.count()}")
            
            print("\n✅ تولید داده‌های فیک با موفقیت انجام شد!")
            print("\n🔹 اطلاعات لاگین تست:")
            print("   ادمین: username='admin', password='admin123'")
            print("   کاربران عادی: password='testpass123' برای همه")
            print("=" * 50)
            
    except Exception as e:
        print(f"❌ خطا در تولید داده‌ها: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run()