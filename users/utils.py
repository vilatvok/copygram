import redis

from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from django.shortcuts import render

from plotly.graph_objs import Bar, Layout
from plotly import offline

from .models import Action, Follower
from datetime import timedelta

from mainsite.models import Post

r = redis.Redis(host="redis", port=6379, db=0)


def create_action(owner, act, img=None, target=None):
    inter = timezone.now() - timedelta(minutes=5)
    similar = Action.objects.filter(owner=owner, act=act, image=img, date__gte=inter)

    if target:
        target_ct = ContentType.objects.get_for_model(target)
        similar_actions = similar.filter(tc=target_ct, ti=target.id)

    if not similar_actions:
        action = Action.objects.create(owner=owner, act=act, image=img, target=target)
        action.save()
        return True
    return False


def get_res(request):
    users = get_user_model().objects.all()

    f = []
    for i in list(users):
        f.append(Post.objects.filter(owner=i).count())

    x_val = [user.username for user in list(users)]
    data = [Bar(x=x_val, y=f)]

    x_axis = {"title": "users"}
    y_axis = {"title": "count of posts"}

    my_lay = Layout(title="Results", xaxis=x_axis, yaxis=y_axis)
    offline.plot(
        {"data": data, "layout": my_lay},
        filename="users/templates/users/statistics.html",
        auto_open=False,
    )
    return render(request, "users/statistics.html")


class Recommender:
    def get_key(self, user):
        return f"user:{user.id}:similar"
    
    def add_suggestions(self, user, others):
        for other in others:
            if not Follower.objects.filter(user_from=user, user_to=other).exists():
                r.zincrby(self.get_key(user), 1, other.id)

    def remove_suggestions(self, user, others):
        users = [other.id for other in others]
        r.zrem(self.get_key(user), *users)
    
    def suggests_for_user(self, user):
        suggestions = r.zrange(self.get_key(user), 0, -1, desc=True)
        suggestions_users_ids = [int(s) for s in suggestions]

        suggestions_users = get_user_model().objects.filter(id__in=suggestions_users_ids)
        return suggestions_users