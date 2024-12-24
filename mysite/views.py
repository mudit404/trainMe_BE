from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password, make_password
from .models import User, Course
from .serializers import UserSerializer, CourseSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
import stripe
from django.http import JsonResponse
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY
class SignupView(APIView):
    def post(self, request):
        # Get data from the request
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            return Response({'error': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

        # Create new user
        user = User.objects.create(
            email=email,
            username=username,
            password=make_password(password),  # Hash the password
        )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'message': 'User created successfully',
            'token': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    def post(self, request):
        # Get username and password from the request body
        username = request.data.get('username')
        password = request.data.get('password')

        try:
            # Fetch the user by username instead of email
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Logged in successfully',
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class CourseView(APIView):
    """
    Handle both GET (list courses) and POST (create a course) requests for courses.
    """
    # Set permission classes
    permission_classes = [AllowAny]  # Default permission for GET requests (open to everyone)
    
    def get(self, request, course_id=None):
        """
        Retrieve a list of all courses (GET request).
        This view is open to everyone.
        """
        if course_id:
            # Fetch a specific course by ID
            try:
                course = Course.objects.get(id=course_id)
                serializer = CourseSerializer(course)
                return Response({
                    'course': serializer.data
                }, status=status.HTTP_200_OK)
            except Course.DoesNotExist:
                return Response({
                    'error': 'Course not found.'
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Fetch all courses if no course_id is provided
            courses = Course.objects.all()  # Fetch all courses
            serializer = CourseSerializer(courses, many=True)
            return Response({
                'courses': serializer.data
            }, status=status.HTTP_200_OK)
    
    def post(self, request):
        """
        Create a new course (POST request).
        This view requires the user to be authenticated.
        """
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required to create a course.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Ensure the necessary data is provided in the request
        title = request.data.get('title')
        description = request.data.get('description')
        image_url = request.data.get('image_url', None)  # Image URL is optional

        if not title or not description:
            return Response({
                'error': 'Title and description are required.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Create the new course
        course = Course.objects.create(
            title=title,
            description=description,
            image_url=image_url,  
        )

        # Serialize the course data
        serializer = CourseSerializer(course)

        # Return success response with the serialized course data
        return Response({
            'message': 'Course created successfully',
            'course': serializer.data
        }, status=status.HTTP_201_CREATED)
    
class CreateCheckoutSessionView(APIView):
    """
    This view creates a Stripe checkout session to initiate the payment process.
    """
    # permission_classes = [IsAuthenticated]  # Only authenticated users can initiate the payment

    def post(self, request):
        # Get the user and course details from the request body
        course_id = request.data.get('course_id')
        user_id = request.user.id  # Assuming user is authenticated and using JWT

        # Get the course from the database
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Create a Stripe Checkout session
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',  # Use your desired currency
                            'product_data': {
                                'name': course.title,
                                'description': course.description,
                                'images': [course.image_url],  # Optional: Image URL for the product
                            },
                            'unit_amount': 1000 * 100,  # Stripe requires price in the smallest unit (e.g., paise for INR)
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=request.build_absolute_uri('/success/?session_id={CHECKOUT_SESSION_ID}'),
                cancel_url=request.build_absolute_uri('/cancel/'),
                metadata={
                    'user_id': user_id,  # Pass the user ID to link the purchase with the user
                    'course_id': course.id,  # Pass the course ID to know which course was purchased
                },
            )

            return JsonResponse({
                'id': session.id
            })

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
