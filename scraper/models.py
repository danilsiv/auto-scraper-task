from django.db import models

from utils.validators import validate_formatted_phone


class Car(models.Model):
    url = models.URLField(unique=True, db_index=True)
    title = models.CharField(max_length=255)
    price_usd = models.PositiveIntegerField()
    odometer = models.PositiveIntegerField()
    username = models.CharField(max_length=255)
    phone_number = models.CharField(
        max_length=12,
        validators=[validate_formatted_phone]
    )
    image_url = models.URLField()
    images_count = models.PositiveIntegerField()
    car_number = models.CharField(max_length=20, blank=True, null=True)
    car_vin = models.CharField(max_length=50, blank=True, null=True)
    datetime_found = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-datetime_found"]

    def __str__(self) -> str:
        return f"{self.title} ({self.price_usd} USD)"
