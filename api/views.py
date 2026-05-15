# api/views.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API views — handle HTTP requests and return responses.
# Each view is one endpoint in our API.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import User, Diagnosis, UserFeedback
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    DiagnosisSerializer,
    DiagnoseRequestSerializer,
    UserFeedbackSerializer,
)
from ml.predictor import CropDiseasePredictor


# ── AUTHENTICATION ENDPOINTS ─────────────────────────

@swagger_auto_schema(
    method='post',
    request_body=RegisterSerializer,
    responses={201: UserSerializer}
)
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/h', block=True)
def register(request):
    """
    Register a new farmer account.
    Rate limited to 5 registrations per hour per IP.
    """
    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        # Create the user
        user = serializer.save()

        # Generate JWT tokens immediately after registration
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'Account created successfully.',
            'user': UserSerializer(user).data,
            'tokens': {
                'access':  str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', block=True)
def login(request):
    """
    Login with username and password.
    Returns JWT access and refresh tokens.
    Rate limited to 5 attempts per minute per IP.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    # Validate that both fields were provided
    if not username or not password:
        return Response(
            {'error': 'Username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Authenticate user
    user = authenticate(username=username, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid username or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    # Generate tokens
    refresh = RefreshToken.for_user(user)

    return Response({
        'message': 'Login successful.',
        'user': UserSerializer(user).data,
        'tokens': {
            'access':  str(refresh.access_token),
            'refresh': str(refresh),
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout by blacklisting the refresh token.
    Requires: refresh token in request body.
    """
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        # Blacklist this token — cannot be used again
        token.blacklist()
        return Response({'message': 'Logged out successfully.'})
    except Exception:
        return Response(
            {'error': 'Invalid token.'},
            status=status.HTTP_400_BAD_REQUEST
        )


# ── USER ENDPOINTS ───────────────────────────────────

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    GET  — Returns current user profile.
    PUT  — Updates current user profile.
    """
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True  # Allow partial updates
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ── DIAGNOSIS ENDPOINTS ──────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='20/d', block=True)
def diagnose(request):
    """
    Upload a leaf photo and get disease diagnosis.
    Rate limited to 20 diagnoses per day per user.

    Steps:
    1. Validate the uploaded image
    2. Run ML model prediction
    3. Save diagnosis to database
    4. Return results to farmer
    """

    # Step 1 — Validate the image
    serializer = DiagnoseRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    image = serializer.validated_data['image']

    # Step 2 — Run ML prediction
    try:
        prediction = CropDiseasePredictor.predict(image)
    except Exception as e:
        return Response(
            {'error': f'Prediction failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Step 3 — Save to database
    image.seek(0)  # Reset file pointer before saving
    diagnosis = Diagnosis.objects.create(
        user=request.user,
        image=image,
        disease_name=prediction['disease_name'],
        friendly_name=prediction['friendly_name'],
        confidence=prediction['confidence'],
        treatment=prediction['treatment'],
        severity=prediction['severity'],
        crop_type=prediction['crop_type'],
    )

    # Step 4 — Return results
    response_data = DiagnosisSerializer(diagnosis).data

    # Add warning if confidence is low
    if prediction['low_confidence_warning']:
        response_data['warning'] = (
            "Model confidence is below 70%. "
            "Please consult an agricultural officer "
            "to confirm this diagnosis."
        )

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def diagnosis_history(request):
    """
    Returns all past diagnoses for the current user.
    Newest diagnoses shown first.
    """
    diagnoses = Diagnosis.objects.filter(
        user=request.user
    ).order_by('-created_at')

    serializer = DiagnosisSerializer(diagnoses, many=True)
    return Response(serializer.data)


@api_view(['GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def diagnosis_detail(request, diagnosis_id):
    """
    GET    — Returns one specific diagnosis.
    DELETE — Deletes one specific diagnosis.
    Users can only access their own diagnoses.
    """
    try:
        # Ensure user can only see their own diagnoses
        diagnosis = Diagnosis.objects.get(
            id=diagnosis_id,
            user=request.user
        )
    except Diagnosis.DoesNotExist:
        return Response(
            {'error': 'Diagnosis not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == 'GET':
        serializer = DiagnosisSerializer(diagnosis)
        return Response(serializer.data)

    elif request.method == 'DELETE':
        diagnosis.delete()
        return Response(
            {'message': 'Diagnosis deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ── FEEDBACK ENDPOINT ────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_feedback(request, diagnosis_id):
    """
    Farmer confirms whether diagnosis was accurate.
    This data is used to improve the ML model.
    """
    try:
        diagnosis = Diagnosis.objects.get(
            id=diagnosis_id,
            user=request.user
        )
    except Diagnosis.DoesNotExist:
        return Response(
            {'error': 'Diagnosis not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if feedback already submitted
    if hasattr(diagnosis, 'feedback'):
        return Response(
            {'error': 'Feedback already submitted for this diagnosis.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer = UserFeedbackSerializer(data={
        'diagnosis':    diagnosis.id,
        'was_accurate': request.data.get('was_accurate'),
        'comment':      request.data.get('comment', ''),
    })

    if serializer.is_valid():
        serializer.save()
        return Response(
            {'message': 'Thank you for your feedback!'},
            status=status.HTTP_201_CREATED
        )

    return Response(
        serializer.errors,
        status=status.HTTP_400_BAD_REQUEST
    )


# ── ADMIN ENDPOINTS ──────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats(request):
    """
    Returns system statistics.
    Only accessible by admin/staff users.
    """

    # Only staff can access stats
    if not request.user.is_staff:
        return Response(
            {'error': 'Admin access required.'},
            status=status.HTTP_403_FORBIDDEN
        )

    total_users      = User.objects.count()
    total_diagnoses  = Diagnosis.objects.count()
    total_feedback   = UserFeedback.objects.count()
    accurate_count   = UserFeedback.objects.filter(
        was_accurate=True
    ).count()

    # Calculate accuracy rate from user feedback
    accuracy_rate = (
        (accurate_count / total_feedback * 100)
        if total_feedback > 0 else 0
    )

    # Count by disease
    from django.db.models import Count
    top_diseases = (
        Diagnosis.objects
        .values('friendly_name')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )

    return Response({
        'total_users':     total_users,
        'total_diagnoses': total_diagnoses,
        'total_feedback':  total_feedback,
        'accuracy_rate':   f'{accuracy_rate:.1f}%',
        'top_diseases':    list(top_diseases),
    })