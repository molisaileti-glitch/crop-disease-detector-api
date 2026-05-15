# api/serializers.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Serializers convert Django models to JSON
# and validate incoming data from Flutter app.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Diagnosis, UserFeedback


class RegisterSerializer(serializers.ModelSerializer):
    """
    Validates and creates a new user account.
    Used by the /auth/register/ endpoint.
    """

    # Password field — write only, never returned in response
    password = serializers.CharField(
        write_only=True,
        required=True,
        # Use Django's built in password validators
        validators=[validate_password]
    )

    # Confirm password — must match password
    password2 = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'phone_number',
            'location',
            'password',
            'password2'
        ]

    def validate(self, data):
        """
        Check that both passwords match.
        Runs before saving the user.
        """
        if data['password'] != data['password2']:
            raise serializers.ValidationError(
                {"password": "Passwords do not match."}
            )
        return data

    def create(self, validated_data):
        """
        Create new user with hashed password.
        Remove password2 since it is not a model field.
        """
        # Remove confirm password — not needed for creation
        validated_data.pop('password2')

        # create_user automatically hashes the password
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Returns user profile data.
    Never returns password.
    """

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'phone_number',
            'location',
            'created_at'
        ]
        # These fields cannot be changed via API
        read_only_fields = ['id', 'created_at']


class DiagnosisSerializer(serializers.ModelSerializer):
    """
    Returns diagnosis data including
    disease name, confidence and treatment.
    """

    # Include username in response
    username = serializers.CharField(
        source='user.username',
        read_only=True
    )

    class Meta:
        model = Diagnosis
        fields = [
            'id',
            'username',
            'image',
            'disease_name',
            'friendly_name',
            'confidence',
            'treatment',
            'severity',
            'crop_type',
            'created_at'
        ]
        read_only_fields = [
            'id',
            'disease_name',
            'friendly_name',
            'confidence',
            'treatment',
            'severity',
            'crop_type',
            'created_at'
        ]


class DiagnoseRequestSerializer(serializers.Serializer):
    """
    Validates incoming image upload request.
    Checks file size, type and dimensions.
    """

    image = serializers.ImageField(required=True)

    def validate_image(self, image):
        """
        Validates the uploaded image:
        - Must be JPEG or PNG
        - Must be under 2MB
        - Must be at least 100x100 pixels
        - Must be at most 4000x4000 pixels
        """
        from django.conf import settings
        from PIL import Image as PILImage

        # Check file size — max 2MB
        if image.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(
                "Image too large. Maximum size is 2MB."
            )

        # Check content type
        if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError(
                "Invalid file type. Only JPEG and PNG allowed."
            )

        # Check actual file content — not just extension
        # Prevents someone renaming malware.exe to image.jpg
        try:
            img = PILImage.open(image)
            img.verify()
        except Exception:
            raise serializers.ValidationError(
                "Invalid image file. File may be corrupted."
            )

        # Check dimensions
        image.seek(0)  # Reset file pointer after verify
        img = PILImage.open(image)
        width, height = img.size

        if width < settings.MIN_IMAGE_DIMENSION or \
           height < settings.MIN_IMAGE_DIMENSION:
            raise serializers.ValidationError(
                f"Image too small. Minimum {settings.MIN_IMAGE_DIMENSION}x"
                f"{settings.MIN_IMAGE_DIMENSION} pixels."
            )

        if width > settings.MAX_IMAGE_DIMENSION or \
           height > settings.MAX_IMAGE_DIMENSION:
            raise serializers.ValidationError(
                f"Image too large. Maximum {settings.MAX_IMAGE_DIMENSION}x"
                f"{settings.MAX_IMAGE_DIMENSION} pixels."
            )

        image.seek(0)  # Reset for saving
        return image


class UserFeedbackSerializer(serializers.ModelSerializer):
    """
    Validates farmer feedback on diagnosis accuracy.
    """

    class Meta:
        model = UserFeedback
        fields = ['id', 'diagnosis', 'was_accurate', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']