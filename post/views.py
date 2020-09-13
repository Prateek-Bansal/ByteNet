from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
import os
from django.db.models import F, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from accounts.models import UserProfileInfo, User
from .models import Post, TagNotification
from .forms import PostForm
from feed.views import feed
from django.http import HttpResponse
from post.imgur_client import upload_image
try:
    from django.utils import simplejson as json
except ImportError:
    import json


@login_required
def create_post(request):
    #print("Cretaing Post")
    user = request.user
    if request.method == "POST":
        text = request.POST.get("text")
        from_feed = request.POST.get("from_feed")
        if text == "":
            return feed(request)
        tagged_friends = request.POST.getlist("checkbox_tag")
        try:
            post = Post.objects.create(text=text, author=request.user, time_of_posting = timezone.now())
        except Exception as e:
            raise e
        file = None
        print("hehe")
        try:
            file = request.FILES['image']
            file = upload_image(file)
            post.imgur_url = file
            print("Got the file")
        except Exception as e:
            print(e)
        # post.save()
        for friend in tagged_friends:
            tagged_friend = User.objects.get(username=friend)
            post.tags.add(tagged_friend)
            tag_notif = TagNotification.objects.create(post=post, 
                                        tagged_user=tagged_friend, time_of_tagging=timezone.now())
        post.save()
        if from_feed:
            return JsonResponse({"text":text,
                                 "pk": post.pk,
                                "like_btn_class": "btn-outline-success",
                                "dislike_btn_class" :"btn-outline-danger", 
                                "num_dislikes": 0, 
                                "num_likes": 0})
        return redirect("feed:news_feed")
    else:
        form = PostForm()
        friends = UserProfileInfo.objects.filter(user=user
                                                ).annotate(friend_name=F("friend__username"
                                                )).values("friend_name")
        friends_list = list()
        for friend in friends:
            friends_list.append(friend["friend_name"])
        friends_exist = True
        if not friends:
            friends_exist = False
        return render(request, 'post/new_post.html', {'friends':list(friends),
                            "friends_list": friends_list,
                             'friends_exist':friends_exist})

@login_required
def view_post(request, post_id):
    post_object = None
    try:
        post_object = Post.objects.get(pk=post_id)
    except Post.DoesNotExist:
        return render(request, "post/post_not_found.html", {})

    if post_object:
        print(post_object)
        post = Post.objects.filter(pk=post_id).values("author__username", "time_of_posting", "pk",
                                 "text", "tags__username", "is_edited")
        tagged_users = list()
        for post_ins in post:
            tag_name = post_ins["tags__username"]
            if tag_name is not None:
                tagged_users.append(tag_name)
        post = post[0]
        
        post["tags__username"] = tagged_users
        #print(post_object.likes.all())
        post["num_likes"] = post_object.total_likes()
        post["num_dislikes"] = post_object.total_dislikes()
        post["liked"] = post_object.likes.filter(pk=request.user.pk).exists()
        post["disliked"] = post_object.dislikes.filter(pk=request.user.pk).exists() 
        post["image"] = post_object.imgur_url
        post["approved"] = post_object.img_approved
        current_user = False
        if post["author__username"] == request.user.username:
            current_user = True
        #print("works?")

        return render(request, "post/view_post.html", {"post":post, "current_user":current_user})
    else:
        return render(request, "post/post_not_found.html", {})

@login_required
def edit_post(request, pk):
    print("Edit post")
    try:
        post = Post.objects.get(pk=pk, author=request.user)
        print("Found post")
    except Post.DoesNotExist:
        return render(request, 'accounts/index.html', {})
    if request.method == "POST":
        text = request.POST.get("text")
        if text == "":
            return feed(request)
        post.text = text
        post.is_edited = True
        post.save()
        return view_post(request, post.pk)
    else:
        form = dict()
        form["text"] = post.text
        form["time"] = post.time_of_posting
        form["tags"] = post.tags.all()
        form["pk"] = pk
        print(form["tags"])
        return render(request, 'post/edit_post.html', {'form': form})

@login_required
def delete_post(request, pk):
    print("Delete post")
    try:
        post = Post.objects.get(pk=pk, author=request.user)
        print("Found post")
    except Post.DoesNotExist:
        return render(request, 'accounts/index.html', {})
    if request.method == "POST":
        print("confirmation accepted deleteing ")
        post.delete()
    else:
        print("confirm delete")
        post_details = dict()
        post_details["id"] = pk
        return render(request, "post/post_delete_confirmation.html", {"post": post_details})
    return render(request, 'accounts/index.html', {})
        
@login_required
def posts_list(request, author=None):
    current_user = False
    if author is None:
        author = request.user.username
        current_user = True
    print("Fetching all posts of ", author)
    posts = Post.objects.filter(author__username=author).order_by('-time_of_posting'
                                ).values("text", "pk")
    #print(list(posts))
    posts_exist = True
    if not posts:
        posts_exist = False        
    #print("post is None?", posts is None)
    print(current_user, posts_exist)
    return render(request, "post/posts_list.html", {"posts":posts, "mention":False, 
                                                    "author":author, 
                                                    "posts_exist":posts_exist, 
                                                    "current_user":current_user })

@login_required
def view_mentions(request):
    user = request.user
    print("Fetching mentions ")
    posts = TagNotification.objects.filter(tagged_user=user).order_by('-post__time_of_posting')
    if posts:
        posts = posts.values("post__text","post__pk", "post__author__username",
                                                  "post__time_of_posting")
        print(posts)
        return render(request, "post/posts_list.html", {"posts":posts, "mention":True, "posts_exist":True})
    else:
        return render(request, "post/posts_list.html", {"posts":posts, "mention":True, "posts_exist":False})

@login_required
@require_POST
def like_post(request):
    like_btn_class = None
    dislike_btn_class = None
    user = request.user
    if request.method == "POST":
        #print("Atleast, this works.")
        post_id = request.POST.get("post_id")
        #print(post_id)
        post = Post.objects.get(pk=post_id)
        
        if post.likes.filter(pk=user.pk).exists(): 
            # user has already liked this post
            # remove like/user
            post.likes.remove(user)
            post.save()
            #print(post.likes.all())
            message = "Ummm, I don't know wheteher I like it or not"
            #print("post unliked")
            like_btn_class = "btn-outline-success"
            dislike_btn_class = "btn-outline-danger"
        else:
            # add a new like for a post
            like_btn_class = "btn-success"
            dislike_btn_class = "btn-outline-danger"
            if post.dislikes.filter(pk=user.pk).exists():
                post.dislikes.remove(user)
                post.save()
            post.likes.add(user)
            post.save()
            #print(post.likes.all())
            message = "Wow! this one was cool"
        num_dislikes = post.total_dislikes()
        num_likes = post.total_likes()

    # use mimetype instead of content_type if django < 5
    return JsonResponse({"message":message,
                         "like_btn_class": like_btn_class,
                         "dislike_btn_class" :dislike_btn_class, 
                         "num_dislikes": num_dislikes, 
                         "num_likes": num_likes}) # Sending an success response

@login_required
@require_POST
def dislike_post(request):
    user = request.user
    if request.method == "POST":
        post_id = request.POST.get("post_id")
        #print(post_id)
        post = Post.objects.get(pk=post_id)
        #print(post)
        #print("User", user.pk)
        if post.dislikes.filter(pk=user.pk).exists():
            post.dislikes.remove(user)
            post.save()
            message = "Yeah okay, I guess it's not that bad"
            like_btn_class = "btn-outline-success"
            dislike_btn_class = "btn-outline-danger"
            #print("post undisliked")
        else:
            # add a new like for a post
            like_btn_class = "btn-outline-success"
            dislike_btn_class = "btn-danger"
            post.dislikes.add(user)
            if post.likes.filter(pk=user.pk).exists():
                post.likes.remove(user)
                post.save()
            post.save()
            message = "Nah, I don't like this"
        num_dislikes = post.total_dislikes()
        num_likes = post.total_likes()
    return JsonResponse({"message":message,
                         "like_btn_class": like_btn_class,
                         "dislike_btn_class" :dislike_btn_class, 
                         "num_dislikes": num_dislikes, 
                         "num_likes": num_likes}) 




@staff_member_required
def get_unapprove_images(request):
    unapprove = list()
    try:
        images = Post.objects.exclude(imgur_url=None).filter(img_approved=False).values("imgur_url", "pk")
        for i in images:
            image_link = i["imgur_url"] 
            if image_link != "":
                unapprove.append({"image":image_link, "pk":i["pk"]})
    except Exception as e:
        print(e)
    # print(unapprove)
    return render(request, 'admin/approve.html', {"posts":unapprove})


@staff_member_required
def get_approve_images(request):
    approve = list()
    try:
        images = Post.objects.exclude(imgur_url=None).filter(img_approved=True).values("imgur_url", "pk")
        for i in images:
            image_link = i["imgur_url"] 
            if image_link != "":
                approve.append({"image":image_link, "pk":i["pk"]})
    except Exception as e:
        print(e)
    return render(request, 'admin/approve.html', {"posts":approve})

@staff_member_required
def approve_images(request):
    post_id = request.POST.get("post")
    # print(post_id)
    post = Post.objects.get(pk=post_id)
    post.img_approved = True
    post.save()
    return get_unapprove_images

@staff_member_required
def delete_images(request):
    post_id = request.POST.get("post")
    post = Post.objects.get(pk=post_id)
    post.imgur_url = None 
    post.save()
    return get_unapprove_images
