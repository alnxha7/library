from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Book, Borrow
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.db.models import Q, F
from django.utils import timezone
from io import BytesIO
from django.http import HttpResponse
from django.db.models import Count
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def home(request):
    return render(request, 'index.html')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        return redirect('login')

    return render(request, 'register.html')

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # Query user by email
            user = User.objects.get(email=email)

            # Check if the password matches
            if check_password(password, user.password):
                login(request, user)
                if user.is_superuser:
                    return redirect('admin_index')
                else:
                    return redirect('user_index')
            else:
                print('Invalid email or password.')
                return redirect('login')

        except User.DoesNotExist:
            print('user does not exist')
            return redirect('login')

    return render(request, 'login.html')

def logout_user(request):
    logout(request)  # Django's built-in logout function
    return redirect('home')
def user_index(request):
    return render(request, 'user_index.html')

def admin_index(request):
    return render(request, 'admin_index.html')

def add_book(request):
    books = Book.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        author = request.POST.get('author')
        quantity = request.POST.get('quantity')

        Book.objects.create(title=title, author=author, quantity=quantity)
        return redirect('add_book')
    

    return render(request, 'add_book.html', {'books': books})

def delete_book(request, book_id):
    book = Book.objects.get(id=book_id)
    book.delete()
    return redirect('add_book')

def edit_book(request, book_id):
    book = Book.objects.get(id=book_id)
    if request.method == 'POST':
        book.author = request.POST.get('author')
        book.title = request.POST.get('title')
        book.quantity = request.POST.get('quantity')
        book.save()
        return redirect('add_book')
    return render(request, 'edit_book.html', {'book': book})

def book_list(request):
    search_query = request.GET.get('search_query', '')
    
    if search_query:
        # Filter books by title or author
        books = Book.objects.filter(title__icontains=search_query) | Book.objects.filter(author__icontains=search_query)
    else:
        # Get all books if no search query
        books = Book.objects.all()

    return render(request, 'add_book.html', {'books': books})

def users(request):
    users = User.objects.filter(is_superuser=False)
    return render(request, 'users.html', {'users': users})

def user_list(request):
    search_query = request.GET.get('search_query', '')
    
    if search_query:
        # Filter users by name or email using Q objects to combine conditions with OR
        users = User.objects.filter(
            Q(username__icontains=search_query) | Q(email__icontains=search_query)
        ).filter(is_superuser=False)  # Make sure to exclude superusers
    else:
        # Get all users if no search query, excluding superusers
        users = User.objects.filter(is_superuser=False)

    return render(request, 'users.html', {'users': users})

def borrow_book(request):
    books = Book.objects.all()
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        
        try:
            book = Book.objects.get(id=book_id)
            
            if book.quantity > 0:
                book.quantity -= 1
                book.save()

                borrow = Borrow(
                    user=request.user,  
                    book=book,
                    borrow_date=timezone.now().date(),
                    return_date=None,  
                )
                borrow.save()

                print(f"You have successfully borrowed {book.title}.")
            else:
                print(f"Sorry, {book.title} is out of stock.")
        
        except Book.DoesNotExist:
            print("Book not found.")

        return redirect('borrow_book')
    return render(request, 'borrow_book.html', {'books': books})

def user_books(request):
    books = Borrow.objects.filter(user=request.user, returned=False)
    if request.method == 'POST':
        borrow_id = request.POST.get('book_id')
        borrow = Borrow.objects.get(id=borrow_id)
        book = borrow.book

        book.quantity += 1
        book.save()

        borrow.return_date = timezone.now().date()
        borrow.returned = True
        borrow.save()
    return render(request, 'user_books.html', {'books': books})

def admin_books(request):
    books = Borrow.objects.all()
    return render(request, 'admin_books.html', {'books': books})

def generate_report(request):
    # Total books available (calculated by subtracting borrowed books from the total quantity)
    total_books = Book.objects.annotate(borrowed_count=Count('borrow')).filter(borrowed_count__lt=F('quantity')).count()

    # Most borrowed books
    most_borrowed_books = Borrow.objects.values('book__title', 'book__author').annotate(borrow_count=Count('book')).order_by('-borrow_count')[:5]

    # List of users with their borrow counts
    user_borrow_counts = Borrow.objects.values('user__username').annotate(borrow_count=Count('user')).order_by('-borrow_count')

    # Create the PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Add report title
    p.setFont("Helvetica", 16)
    p.drawString(200, height - 40, "Library Report")

    # Add Total Books Available
    p.setFont("Helvetica", 12)
    p.drawString(40, height - 80, f"Total Books Available: {total_books}")

    # Add Most Borrowed Books
    p.drawString(40, height - 120, "Most Borrowed Books:")
    y_position = height - 140
    p.setFont("Helvetica", 10)
    for book in most_borrowed_books:
        p.drawString(40, y_position, f"Title: {book['book__title']}, Author: {book['book__author']}, Borrow Count: {book['borrow_count']}")
        y_position -= 20

    # Add Users and Borrow Counts
    p.drawString(40, y_position - 40, "Users with Borrow Counts:")
    y_position -= 60
    for user in user_borrow_counts:
        p.drawString(40, y_position, f"User: {user['user__username']}, Borrow Count: {user['borrow_count']}")
        y_position -= 20

    # Save PDF
    p.showPage()
    p.save()

    # Return the PDF as a response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="library_report.pdf"'
    return response