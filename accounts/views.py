from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from accounts.forms import UserForm, UserProfileInfoForm
from accounts.models import User, UserProfileInfo
from helpers.profile_picture_generator import generate_profile_pic
from helpers.imgur_client import upload_image
# Create your views here.

def index(request):
    return render(request, 'accounts/index.html')

@login_required
def special(request):
    return HttpResponse("You are logged in.")

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))

def register(request):
    registered = False
    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileInfoForm(data=request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.set_password(user.password)
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.profile_pic_url = generate_profile_pic(user.username)
            profile.save()
            registered = True
        else:
            print(user_form.errors, profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = UserProfileInfoForm()
    return render(request, 'accounts/register.html', {'user_form' : user_form, 
                                                      'profile_form' : profile_form, 
                                                      'registered' : registered})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect(reverse('index'))
            else:
                return HttpResponse('Your account is inactive')
        else:
            print('Someone tried to login and failed')
            print(f"They used username: {username} and password: {password}")
            return render(request, 'accounts/login.html', {"error":True, "error_message":"Invalid Credentials"})
    else:
        return render(request, 'accounts/login.html', {})

@login_required
def delete_account(request):
    user = request.user
    if request.method == "POST":
        print("Deleting account ", user.username)
        User.objects.get(username=user.username).delete()
        print("Account deleted")
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, "accounts/account_delete_confirmation.html", {"username":user.username})


@login_required
def edit_account(request):
    error = False
    message = ""
    user = request.user
    #print("finding user")
    user = User.objects.filter(username=user.username).values("pk", "email", "username", 
                                                                "last_name", "first_name")
    #print("user found")
    user_profile = UserProfileInfo.objects.filter(user=request.user).values("age", "location")
    new_username = request.user.username
    if request.method == "POST":
        new_username = request.POST.get("username")
        any_user = User.objects.filter(username=new_username).exists()
        if request.user.username == new_username or not any_user :
            user_profile = UserProfileInfo.objects.get(user=request.user)
            user = User.objects.get(pk=request.user.pk)
            # print("checkpoint a")
            new_location = request.POST.get("location")
            new_email = request.POST.get("email")
            new_age = request.POST.get("age")
            new_first_name = request.POST.get("first_name")
            new_last_name = request.POST.get("last_name")
            
            user_profile.age = new_age
            user_profile.location = new_location
            print(user_profile.profile_pic_url)
            # file = request.FILES['image']
            print(request.FILES.keys())
            try:
                print("What")
                file = request.FILES['image']
                print(file)
                file, _ = upload_image(file)
                user_profile.profile_pic_url = file
                print(file)
            except Exception as e:
                print(e)
            print(user_profile.profile_pic_url)
            user_profile.save()
            user.email = new_email
            user.username = new_username
            #user.set_password(new_password)
            user.first_name = new_first_name
            user.last_name = new_last_name
            user.save()
            return render(request, "accounts/edit_successful.html", {})
        else:
            error = True
            message = "Username already taken"
    
    print("Edit account")    
    form = dict()
    user = user[0]
    user_profile = user_profile[0]
    form["username"] = new_username
    #print(user)
    form["email"] = user["email"]
    form["pk"] = user["pk"]
    form["age"] = user_profile["age"]
    form["location"] = user_profile["location"]
    form["first_name"] = user["first_name"]
    form["last_name"] = user["last_name"]
    return render(request, "accounts/edit_account.html", 
                            {"form":form, "error":error, "message":message})