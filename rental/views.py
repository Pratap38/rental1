from django.shortcuts import render,redirect,get_object_or_404
from .models import Car,Profile,Promocode,Rental
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.utils.timezone import now
from datetime import timedelta
from django.utils import timezone


def logout_view(request):
    if request.method == 'GET':  # accept GET request
        logout(request)
        return redirect('login')
# Create your views here
def home(request):
    cars = Car.objects.filter(isavailable=True).order_by('-created_at')[:3]
    return render(request, 'home.html', {'cars': cars})

def search_car(request):
    cities= Car.objects.values_list('available_city', flat=True).distinct()
    cars=None
    search_city=None
    if request.method == 'GET' and 'city' in request.GET:
        selected_city = request.GET['city']
        cars = Car.objects.filter(available_city=selected_city, isavailable=True)

    return render(request, 'search.html', {
        'cities': cities,
        'cars': cars,
        'selected_city': selected_city
    })

def car_list(request, car_type="ALL"):
    if car_type and car_type != "ALL":
        cars = Car.objects.filter(car_type=car_type.upper(), isavailable=True)
    else:
        cars = Car.objects.filter(isavailable=True)

    context = {
        "cars": cars,
        "selected_type": car_type.upper() if car_type else "ALL"
    }
    return render(request, "cars.html", context)
@login_required()
def profile(request):
    profile = request.user.profile  # access the Profile linked to the logged-in User
    last_order = request.user.orders.order_by("-created_at").first()
    return render(request, "profile.html", {"profile": profile, "last_order": last_order})
def signup(request):
    if request.method == "POST":
        fullname = request.POST.get('fullname', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()

        # Basic validations
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'signup.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'signup.html')

        try:
            # Create user
            user = User.objects.create_user(username=username, email=email, password=password, first_name=fullname)
            
            # Create profile only if it doesn't exist
            Profile.objects.get_or_create(user=user, defaults={'phone': phone, 'address': address})

            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')  # Make sure 'login' URL name exists
        except IntegrityError:
            messages.error(request, "A profile for this user already exists.")
            return render(request, 'signup.html')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'signup.html')

    return render(request, 'signup.html')
def service(request):
    return render(request,"service.html")
def car_detail(request, car_id):
    car = Car.objects.get(id=car_id)
    return render(request, 'details.html', {'car': car})

def view_cart(request):
    cart = request.session.get('cart', [])
    cars = Car.objects.filter(id__in=[int(cid) for cid in cart])

    cart_items = []
    for car in cars:
        # for now, use dummy values until you implement booking logic
        days = 1  
        subtotal = car.current_price * days
        tax = subtotal * 0.08875
        service_fee = 25
        total_price = subtotal + tax + service_fee

        cart_items.append({
            'id': car.id,
            'car': car,
            'pickup_date': None,   # to be filled later
            'return_date': None,   # to be filled later
            'days': days,
            'subtotal': subtotal,
            'tax': tax,
            'total_price': total_price,
            'location': car.available_city,
        })

    subtotal_all = sum(item['subtotal'] for item in cart_items)
    tax_total = sum(item['tax'] for item in cart_items)
    service_fee_total = 2225 if cart_items else 0
    grand_total = subtotal_all + tax_total + service_fee_total

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal_all,
        'tax_total': tax_total,
        'service_fee_total': service_fee_total,
        'grand_total': grand_total,
    })

@login_required(login_url='login')
def add_to_cart(request, car_id):
     car = get_object_or_404(Car, id=car_id)

   
     cart = request.session.get('cart', [])

    
     car_id_str = str(car_id)

   
     if car_id_str not in cart:
        cart.append(car_id_str)

  
     request.session['cart'] = cart
     request.session.modified = True

     return redirect('cart')
     return redirect('cart')
def cart_count(request):
    cart = request.session.get('cart', [])
    return {'cart_count': len(cart)}
def remove_from_cart(request, item_id):
      if request.method == "POST":
        cart = request.session.get('cart', [])
        item_id_str = str(item_id)  # match session storage type

        if item_id_str in cart:
            cart.remove(item_id_str)
            request.session['cart'] = cart
            request.session.modified = True

        return JsonResponse({"success": True})

      return JsonResponse({"success": False}, status=400)
def checkout(request):
    cart = request.session.get('cart', [])
    cars = Car.objects.filter(id__in=[int(cid) for cid in cart])

    cart_items = []
    for car in cars:
        days = 1  # dummy for now
        subtotal = car.current_price * days
        tax = subtotal * 0.08875
        service_fee = 25
        total_price = subtotal + tax + service_fee

        cart_items.append({
            'id': car.id,
            'car': car,
            'pickup_date': None,  # to be filled later
            'return_date': None,  # to be filled later
            'days': days,
            'subtotal': subtotal,
            'tax': tax,
            'total_price': total_price,
            'location': car.available_city,
        })

    subtotal_all = sum(item['subtotal'] for item in cart_items)
    tax_total = sum(item['tax'] for item in cart_items)
    service_fee_total = 2225 if cart_items else 0
    grand_total = subtotal_all + tax_total + service_fee_total

    if request.method == 'POST':
        # Save all cart items as Rental objects
        for item in cart_items:
            Rental.objects.create(
                user=request.user,
                car=item['car'],
                start_date=timezone.now(),  # or get from form
                end_date=timezone.now() + timezone.timedelta(days=item['days']),
                pickup_location=item['location'],
                dropoff_location=item['location'],
                price_per_day=item['car'].current_price,
                total_price=item['total_price'],
                status='Active'
            )
        # Clear cart after checkout
        request.session['cart'] = []
        return redirect('order_history')  # redirect to history page

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'subtotal': subtotal_all,
        'tax_total': tax_total,
        'service_fee_total': service_fee_total,
        'grand_total': grand_total,
    })

def promocode(request):
    if request.method == "POST":
        code =request.POST.get('promocode', '').strip()
        subtotal=float(request.POST.get('subtotal', 0))
        try:
            promo=Promocode.objects.get(code=code, active=True)
            discount=(promo.discount_per/100)*subtotal
            new_total=subtotal-discount
            return JsonResponse({
                "success": True,
                "discount": promo.discount_per,
                "new_total": round(new_total,2)
            })
        except Promocode.DoesNotExist:
            return JsonResponse({
                "success": False,
                "message": "Invalid or inactive promo code."
            })
    return JsonResponse({"success": False, "message": "Invalid request method."}, status=400)
def search_view(request):
    return render(request, 'search.html')
def car_detail_list(request):
    query = request.GET.get("q", "").strip()
    cars = Car.objects.all()

    if query:
        cars = cars.filter(
            Q(car_name__icontains=query) |
            Q(brand__icontains=query) |
            Q(model_name__icontains=query) |
            Q(description__icontains=query)
        )

    return render(request, "search.html", {
        "cars": cars,
        "query": query,
    })
def about(request):
    return render(request,"about.html")
def contact(request):
    return render(request, "contact.html")

def rent_data(request,car_id):
    car=get_object_or_404(Car,pk=car_id)
    if request.user.is_authenticated:
        start_date=now().data()
        end_date = start_date + timedelta(days=1)
        total_price = car.current_price * 1 
        Rental.objects.create(
            user=request.user,
            car=car,
            rental_start_date=start_date,
            rental_end_date=end_date,
            total_price=total_price
        )

        return redirect("order_history")
    else:
        return redirect("login")

def order_history(request):
    rentals = Rental.objects.filter(user=request.user).order_by('-id')
    last_order = rentals.first() if rentals.exists() else None
    return render(request, 'order_history.html', {'rentals': rentals, 'last_order': last_order})
def luxer(request):
    return render(request, 'luxury_experience.html')
def aeroplane(request):
    return render(request,'airplane_rental_terms.html')