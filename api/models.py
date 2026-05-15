# api/models.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Database models for the crop disease detector.
# Defines what data we store and how it relates.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model extending Django's default.
    We add phone_number and location fields
    specific to our Tanzanian farmer users.
    """

    # Phone number — required for Tanzania users
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        help_text="Tanzanian phone number e.g. 0712345678"
    )

    # Optional location — helps track disease outbreaks
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="City or region e.g. Morogoro, Arusha"
    )

    # When user joined
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.phone_number})"


class Diagnosis(models.Model):
    """
    Stores every crop disease diagnosis.
    Created when a farmer uploads a leaf photo.
    """

    # Severity choices
    SEVERITY_CHOICES = [
        ('none',   'None — Healthy plant'),
        ('low',    'Low — Monitor closely'),
        ('medium', 'Medium — Treatment needed'),
        ('high',   'High — Urgent action required'),
    ]

    # Which user submitted this diagnosis
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='diagnoses'
    )

    # The uploaded leaf image
    # Stored on Cloudinary in production
    image = models.ImageField(
        upload_to='diagnoses/',
        help_text="Uploaded leaf image"
    )

    # ML model prediction results
    disease_name = models.CharField(
        max_length=100,
        help_text="Raw disease class name from ML model"
    )
    friendly_name = models.CharField(
        max_length=100,
        help_text="Human readable disease name"
    )
    confidence = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Model confidence percentage 0-100"
    )

    # Treatment and severity
    treatment = models.TextField(
        help_text="Recommended treatment for this disease"
    )
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='none'
    )

    # Crop type extracted from class name
    crop_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. Tomato, Potato, Pepper"
    )

    # When diagnosis was made
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Show newest diagnoses first
        ordering = ['-created_at']

    def __str__(self):
        return (
            f"{self.user.username} — "
            f"{self.friendly_name} "
            f"({self.confidence}%)"
        )


class UserFeedback(models.Model):
    """
    Farmer feedback on diagnosis accuracy.
    Used to improve the ML model over time.
    """

    # Which diagnosis this feedback is for
    diagnosis = models.OneToOneField(
        Diagnosis,
        on_delete=models.CASCADE,
        related_name='feedback'
    )

    # Was the diagnosis correct?
    was_accurate = models.BooleanField(
        help_text="Did the farmer confirm this diagnosis was correct?"
    )

    # Optional comment from farmer
    comment = models.TextField(
        blank=True,
        help_text="Optional comment from farmer"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        accurate = "Accurate" if self.was_accurate else "Inaccurate"
        return f"{self.diagnosis} — {accurate}"