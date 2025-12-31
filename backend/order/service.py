from .models import Order


def create_order(
    saler,
    customer_name,
    customer_family,
    address,
    postal_code,
    city,
    product,
    total_price,
):
    order = Order.objects.create(
        saler=saler,
        customer_name=customer_name,
        customer_family=customer_family,
        address=address,
        postal_code=postal_code,
        city=city,
        product=product,
        total_price=total_price,
    )
    return order


def get_orders(saler):
    orders = Order.objects.filter(saler=saler)
    return orders


def get_order_saler(order):
    return order.saler


def get_order_customer(order):
    return order.customer_name, order.customer_family


def get_order_product(order):
    return order.product


def get_order_price(order):
    return order.total_price


def get_order_status(order):
    return order.status
