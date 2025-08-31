import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import NutriUser


# ====================
# Register View
# ====================
logger = logging.getLogger(__name__)  # Get a logger for this module

# ====================
# Register View
# ====================
def register_view(request):
    if request.method == 'POST':
        try:
            NutriUser.objects.create(
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                password=request.POST.get('password'),
                age=request.POST.get('age'),
                gender=request.POST.get('gender'),
                health_conditions=request.POST.get('health_conditions'),
                weight=request.POST.get('weight'),
                height=request.POST.get('height'),
                dietary_preferences=request.POST.get('dietary_preferences'),
                goal=request.POST.get('goal')
            )
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')

        except Exception as e:
            logger.error(f"Registration error: {str(e)}")  # Log the error
            messages.error(request, f'Error during registration: {str(e)}')

    return render(request, 'register.html')

# ====================
# Login View
# ====================
def login_view(request):
    # Redirect if already logged in
    if request.session.get('user_id'):
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = NutriUser.objects.get(email=email, password=password)
            request.session['user_id'] = user.id
            messages.success(request, f'Welcome back, {user.name}!')
            return redirect('home')

        except NutriUser.DoesNotExist:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'login.html')


# ====================
# Profile View
# ====================
def profile_view(request):
    user_id = request.session.get('user_id')

    if not user_id:
        return redirect('login')

    try:
        user = NutriUser.objects.get(id=user_id)
    except NutriUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('login')

    if request.method == 'POST':
        try:
            user.name = request.POST.get('name')
            user.email = request.POST.get('email')
            user.password = request.POST.get('password')
            user.age = request.POST.get('age')
            user.gender = request.POST.get('gender')
            user.health_conditions = request.POST.get('health_conditions')
            user.weight = request.POST.get('weight')
            user.height = request.POST.get('height')
            user.bmi = request.POST.get('bmi')
            user.dietary_preferences = request.POST.get('dietary_preferences')
            user.goal = request.POST.get('goal')
            user.save()

            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')

        except Exception as e:
            messages.error(request, f'Error updating profile: {str(e)}')

    return render(request, 'profile.html', {'user': user})


# ====================
# Logout View
# ====================
def logout_view(request):
    request.session.flush()
    messages.info(request, "You have been logged out.")
    return redirect('login')
