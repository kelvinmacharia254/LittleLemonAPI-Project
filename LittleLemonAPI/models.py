from django.db import models

from django.contrib.auth.models import User


# Create your models here.

class Category(models.Model):
    """
    This is Menu Category model. Each menu item belongs to a Category.
    The Category title needs to be indexed by the db as menu items will be searched Category.
    """
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True)


class MenuItem(models.Model):
    """
    MenuItem model.
    Each Menu item belongs to a Category.
    Link to Category via Foreign key.
    """
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)

    def __str__(self):
        return self.title


class Cart(models.Model):
    """
    Cart models is a temporally storage where user can place items before placing an order.
    A user can only have one Cart at time.
    To start a new cart is either an order is placed or the existing one deleted.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    # same item cannot be added twice for the same user but quantities can be increased or reduced.(quantity can vary)
    class Meta:
        unique_together = ('menuitem', 'user')


class Order(models.Model):
    """
    Holds an order as a single item. An order item can have many Order items.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # to refer to same model as foreign key twice in a model. Set on field to have related_name
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='delivery_crew', null=True)
    status = models.BooleanField(db_index=True, default=0)
    total = models.DecimalField(max_digits=6, decimal_places=2)  # total price of all items in the field
    date = models.DateTimeField(db_index=True)  # mark when order was placed


class OrderItem(models.Model):
    """
    When an order is placed. Items moves from Cart to OrderItems table.
    It links to Order table(orderID)
    """
    order = models.ForeignKey(User, on_delete=models.CASCADE)
    menuitem = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    # One order can have one type of menuitem but quantity can vary
    class Meta:
        unique_together = ('order', 'menuitem')
