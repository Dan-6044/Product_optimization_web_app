from django.shortcuts import render, get_object_or_404,redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.utils import timezone
from .models import Subscription
from .models import OptimizationData
from django.contrib.auth.decorators import login_required
import pandas as pd
import subprocess
from django.contrib.auth import logout
from .models import OptimizationData, VisualizationData


def home(request):
    return render(request, 'home.html')

def logout_view(request):
    logout(request)
    return redirect('home')


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        errors = {}

        if User.objects.filter(username=username).exists():
            errors['username'] = 'Username already taken'
        if User.objects.filter(email=email).exists():
            errors['email'] = 'Email already registered'

        if errors:
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)

        # Create user and return success message
        user = User.objects.create_user(username=username, email=email, password=password)
        return JsonResponse({'status': 'success', 'user_id': user.id})  # Include the user ID in the response

    return JsonResponse({'status': 'error', 'errors': {'form': 'Invalid request'}}, status=400)



def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            # Redirect to the dashboard page with the user ID
            return redirect('dashboard', user_id=user.id)
        else:
            return JsonResponse({'status': 'error', 'errors': {'form': 'Invalid username or password'}}, status=400)
    
    return render(request, 'login.html')

def subscription_payment(request):
    # Get the user from the query parameter (user_id)
    user_id = request.GET.get('user_id')
    
    if user_id:
        user = get_object_or_404(User, id=user_id)  # Get the user created during registration
    else:
        return JsonResponse({'status': 'error', 'message': 'User not found'}, status=400)

    if request.method == 'POST':
        country = request.POST.get('country')
        is_company = request.POST.get('isCompany') == 'on'
        payment_method = request.POST.get('paymentMethod')
        subscription_type = request.POST.get('subscription_type')
        
        # Set payment details based on the method
        card_number = request.POST.get('cardNumber') if payment_method == 'creditCard' else None
        expiry_date = request.POST.get('expiryDate') if payment_method == 'creditCard' else None
        cvv = request.POST.get('cvv') if payment_method == 'creditCard' else None

        # Calculate amount and tax based on subscription type
        if subscription_type == 'free':
            amount = 0
            taxes = 0
        elif subscription_type == 'monthly':
            amount = 99
            taxes = amount * 0.03  # 3% tax
        else:  # yearly
            amount = 999
            taxes = amount * 0.06  # 6% tax

        total_amount = amount + taxes

        # Calculate expiration date based on subscription type
        today = timezone.now().date()
        if subscription_type == 'monthly':
            expiration_date = today + timezone.timedelta(days=30)
        elif subscription_type == 'yearly':
            expiration_date = today + timezone.timedelta(days=365)
        else:  # free
            expiration_date = today + timezone.timedelta(days=14)  # 2 weeks for free tier

        # Create a Subscription record in the database
        subscription = Subscription.objects.create(
            user=user,
            country=country,
            is_company=is_company,
            payment_method=payment_method,
            card_number=card_number,
            expiry_date=expiry_date,
            cvv=cvv,
            subscription_type=subscription_type,
            amount=amount,
            taxes=taxes,
            total_amount=total_amount,
            expiration_date=expiration_date
        )

        return redirect(f'/dashboard/{user.id}/')  # Redirect to the dashboard or a success page

    # Render the subscription form for GET requests
    return render(request, 'subscription.html', {'user': user})
    
@login_required
def dashboard(request, user_id=None):
    # If user_id is passed, retrieve that user's data, else use logged-in user
    if user_id:
        user = User.objects.get(id=user_id)
    else:
        user = request.user

    try:
        subscription = Subscription.objects.get(user=user)
    except Subscription.DoesNotExist:
        subscription = None
    
    analysis_count = OptimizationData.objects.filter(user=user).count()  # Adjust based on your model

    context = {
        'user': user,
        'subscription': subscription,
        'analysis_count': analysis_count,
    }
    
    return render(request, 'dashboard.html', context)

@login_required
def upload_excel(request):
    """Upload and process the Excel file."""
    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        
        # Create an OptimizationData instance
        optimization_data = OptimizationData(user=request.user, file=uploaded_file)
        optimization_data.save()

        # Read the uploaded Excel file into a DataFrame
        df = pd.read_excel(optimization_data.file.path)

        # Optional: Process your DataFrame here
        # Example: Converting specific columns to numeric if needed
        if 'column1' in df.columns and 'column2' in df.columns:
            df['column1'] = pd.to_numeric(df['column1'], errors='coerce')
            df['column2'] = pd.to_numeric(df['column2'], errors='coerce')

            # Example operation
            if not df['column1'].isnull().all() and not df['column2'].isnull().all():
                df['result'] = df['column1'] - df['column2']
                # Save the result or process it as needed

        return redirect('excel_dashboard')  # Redirect to the Excel dashboard page

    return render(request, 'dashboard.html')

@login_required
def process_excel_file(optimization_data):
    """Process the Excel file and save data for visualizations."""
    file_path = optimization_data.file.path
    df = pd.read_excel(file_path)

    # Convert datetime columns to string format
    for column in df.select_dtypes(include=['datetime64[ns]', 'datetime']):
        df[column] = df[column].dt.strftime('%Y-%m-%d')  # Convert to string format

    # Example processing for charts
    line_data = df.iloc[:, 1].tolist()  # Assuming the first column for line chart
    bar_data = df.iloc[:, 2].tolist()    # Assuming the second column for bar chart
    pie_data = df.iloc[:, 3].value_counts().to_dict()  # Assuming the third column for pie chart

    # Column chart data (assuming you want to use the first two columns)
    column_data_labels = df.iloc[:, 1].tolist()  # First column as labels
    column_data_values = df.iloc[:, 2].tolist()  # Second column as values

    # Create Pareto chart data (frequency + cumulative percentage)
    value_counts = df.iloc[:, 1].value_counts().sort_index()  # Frequency
    pareto_data = value_counts.cumsum() / value_counts.sum() * 100  # Cumulative percentage
    pareto_labels = value_counts.index.tolist()  # Labels for Pareto chart (x-axis)

    # Waterfall chart data (manually calculated increments)


    # Save processed data in the VisualizationData model
    VisualizationData.objects.create(
        optimization_data=optimization_data,
        chart_type='line',
        data={'labels': list(range(len(line_data))), 'values': line_data}
    )

    VisualizationData.objects.create(
        optimization_data=optimization_data,
        chart_type='bar',
        data={'labels': list(range(len(bar_data))), 'values': bar_data}
    )

    VisualizationData.objects.create(
        optimization_data=optimization_data,
        chart_type='pie',
        data={'labels': list(pie_data.keys()), 'values': list(pie_data.values())}
    )

    # Column chart
    VisualizationData.objects.create(
        optimization_data=optimization_data,
        chart_type='column',
        data={'labels': column_data_labels, 'values': column_data_values}
    )

    # Pareto chart (frequency + cumulative percentage)
    VisualizationData.objects.create(
        optimization_data=optimization_data,
        chart_type='pareto',
        data={
            'labels': pareto_labels,  # X-axis labels
            'frequency_values': value_counts.tolist(),  # Bar data
            'cumulative_values': pareto_data.tolist()  # Line data (cumulative percentage)
        }
    )
  

@login_required
def excel_dashboard(request):
    # Start the Streamlit app in the background
    subprocess.Popen(["streamlit", "run", "path/to/your/streamlit_app.py", "--server.port", "8501"], 
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Render the Django template
    return render(request, "excel_dashboard.html")