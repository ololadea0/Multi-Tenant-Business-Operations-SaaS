from app.api.platform_customer import (
    create_customer,
    delete_customer,
    get_customer,
    get_customer_orders,
    get_customers,
    router,
    update_customer,
)

__all__ = [
    "router",
    "create_customer",
    "get_customers",
    "get_customer_orders",
    "get_customer",
    "update_customer",
    "delete_customer",
]
