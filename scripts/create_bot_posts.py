import random
from accounts.models import UserProfileInfo, User, Friend
from post.models import Post, HashTags, HashTagsPostTable, TaggedPost, TagNotification
from scripts.get_reddit_content import *
from django.utils import timezone
from scripts.probability_generator import get_prob
from helpers.link_preview_generator import get_link_preview

def create_bot_posts():
    users = list(UserProfileInfo.objects.filter(is_bot=True))
    nature_tag = HashTags.objects.get(keyword="nature")
    monster_tag = HashTags.objects.get(keyword="monster")
    sky_tag = HashTags.objects.get(keyword="sky")
    house_tag = HashTags.objects.get(keyword="house")
    space_tag = HashTags.objects.get(keyword="space")
    animal_tag = HashTags.objects.get(keyword="animal")
    arch_tag = HashTags.objects.get(keyword="architecture")
    quote_tag = HashTags.objects.get(keyword="quote")
    plant_tag = HashTags.objects.get(keyword="plants")
    bot_tag = HashTags.objects.get(keyword="bot_post")
    news_tag = HashTags.objects.get(keyword="news")
    til_tag = HashTags.objects.get(keyword="todayilearned")
    think_tag = HashTags.objects.get(keyword="think")
    memes_tag = HashTags.objects.get(keyword="memes")
    harry_tag = HashTags.objects.get(keyword="harrypotter")
    tech_tag = HashTags.objects.get(keyword="technews")
    data_tag = HashTags.objects.get(keyword="data")
    game_tag = HashTags.objects.get(keyword="games")

    quotes = get_quotes()
    til_facts = get_til()
    nature_images = get_earth_images()
    animal_images = get_animal_images()
    sky_images = get_sky_images()
    space_images = get_space_images()
    plant_images = get_plant_images()
    mosnter_images = get_monster_images()
    arch_images = get_arch_images()
    house_images = get_house_images()
    news = get_news()
    beh_monst = get_beh_monster_images()
    thoughts = get_thoughts()
    harry = get_harry()
    memes = get_memes()
    tech = get_tech()
    data = get_data()
    games = get_games()

    contents = thoughts + tech+ harry+quotes+beh_monst+memes + news +data+games
    contents += house_images+ til_facts + nature_images +sky_images +plant_images +animal_images +space_images+mosnter_images+arch_images
    print(len(contents))
    random.shuffle(contents)
    if contents:
        for content in contents:
            if not get_prob():
                continue
            try:
                user = random.choice(users)
                url = content["url"]
                if url:
                    ext = url[-3:]
                    if (content["type"]!="gnews" and content["type"]!="news" and content["type"] != "tech") and ext != "jpg":
                        continue

                post = Post.objects.filter(text=content["text"])
                if post.exists():
                    print("This post exists")
                    continue
                post = Post.objects.create(author_profile=user, author=user.user, 
                                        text=content["text"], time_of_posting=timezone.now(), 
                                        )
                if content["type"] == "news" or content["type"] == "tech" or content["type"] == "gnews":
                    post.article_link = content["url"]
                    # print(content["url"])
                    preview = get_link_preview(content["url"])
                    # print(preview)
                    if preview:
                        post.article_preview = get_link_preview(content["url"])
                else:
                    if content["url"][-3:] == "jpg":
                        post.imgur_url = content["url"]
                        post.img_approved = True
                post.save()
                friends = Friend.objects.filter(source=user)
                if friends.exists():
                    friends = list(friends)
                    l = len(friends)
                    friends = random.sample(friends, min(l, 3))
                    for friend in friends:
                        _ = TaggedPost.objects.create(post=post, user=friend.destination)
                        if not friend.destination.is_bot:
                            _ = TagNotification.objects.create(post=post, time_of_tagging=timezone.now() ,tagged_user=friend.destination.user)
                            print("Tagged a real user")
                        print(f"Tagging {friend.destination.user.username}")
                if content["type"] == "q":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=quote_tag)
                if content["type"] == "th":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=think_tag)
                if content["type"] == "p":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=plant_tag)
                if content["type"] == "til":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=til_tag)
                if content["type"] == "n":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=nature_tag)
                if content["type"] == "a":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=animal_tag)
                if content["type"] == "s":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=sky_tag)
                if content["type"] == "sp":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=space_tag)
                if content["type"] == "h":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=house_tag)
                if content["type"] == "ar":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=arch_tag)
                if content["type"] == "m":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=monster_tag)
                if content["type"] == "news":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=news_tag)
                if content["type"] == "gnews":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=game_tag)
                if content["type"] == "hp":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=harry_tag)
                    post.img_approved = False
                    post.save()
                if content["type"] == "data":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=data_tag)
                if content["type"] == "memes":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=memes_tag)
                    post.img_approved = False
                    post.save()
                if content["type"] == "tech":
                    _ = HashTagsPostTable.objects.create(post=post, hashtag=tech_tag)
                _ = HashTagsPostTable.objects.create(post=post, hashtag=bot_tag)
                print("posted ", post.pk)
            except Exception as e:
                print(e)
