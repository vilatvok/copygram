from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import *

from django.contrib.auth import get_user_model
from django.db.models import Q

from .serializers import *
from .permissions import IsOwner
from .models import *
from .utils import Recommender, create_action
from .tasks import check_story

from mainsite.models import Story, Post
from mainsite.serializers import StorySerializer, PostListSerializer


class UserViewSet(ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsOwner]

    @action(detail=True, methods=["patch"], url_path="pswd")
    def change_pswd(self, request, pk=None):
        user = self.get_object()
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data["password"])
            user.save()
            return Response({"msg": "Changed"})
        return Response({"msg": "Isn't changed"})

    @action(detail=False)
    def posts(self, request):
        post = Post.objects.filter(owner=request.user).select_related("owner")
        serializer = PostListSerializer(
            post, context={"request": request}, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def stories(self, request):
        check_story.delay()
        story = Story.objects.filter(
            owner=request.user).select_related("owner")
        serializer = StorySerializer(story, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def actions(self, request):
        blockf = request.user.block_from.all().values_list("block_to", flat=True)
        blockt = request.user.block_to.all().values_list("block_from", flat=True)
        tc = ContentType.objects.get_for_model(request.user)
        action = (
            Action.objects.filter(tc=tc, ti=request.user.id)
            .exclude(owner__in=set(list(blockf) + list(blockt)))
            .select_related("owner")
            .prefetch_related("target")
        )
        serializer = ActionSerializer(action, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["delete"],
        url_path="act_del",
    )
    def action_delete(self, request, pk=None):
        act = Action.objects.get(pk=pk)
        if request.user == act.owner:
            act.delete()
            return Response({"msg": "deleted"})
        return Response({"msg": "Isn't deleted"})

    @action(detail=False, methods=["get"])
    def followers(self, request):
        followers = Follower.objects.filter(user_to=request.user).select_related(
            "user_from"
        )
        serializer = FollowerSerializer(followers, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def following(self, request):
        following = Follower.objects.filter(user_from=request.user).select_related(
            "user_to"
        )
        serializer = FollowerSerializer(following, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def follow(self, request):
        serializer = FollowerSerializer(data=request.data)
        if serializer.is_valid():
            check = Follower.objects.filter(
                user_from=request.user, user_to=serializer.validated_data["user_to"]
            )
            r = Recommender()
            others = list(
                get_user_model().objects.filter(
                    user_from__user_to=serializer.validated_data["user_to"]
                )
            )
            if check.exists():
                r.remove_suggestions(request.user, others)
                check.delete()
                if Follower.objects.filter(user_from=request.user).exists():
                    r.add_suggestions(
                        request.user, [serializer.validated_data["user_to"]]
                    )
                return Response({"msg": "Unfollowed"})
            else:
                serializer.save(user_from=request.user)
                r.add_suggestions(request.user, others)
                r.remove_suggestions(
                    request.user, [serializer.validated_data["user_to"]]
                )
                create_action(
                    request.user,
                    "following to",
                    target=serializer.validated_data["user_to"],
                )
                return Response(serializer.data)
        return Response(serializer.errors)

    @action(detail=True, methods=["get"])
    def recommendations(self, request, pk=None):
        user = self.get_object()
        r = Recommender()
        rec = r.suggests_for_user(user)
        serializers = UserSerializer(rec, many=True)
        return Response(serializers.data)

    @action(detail=False, methods=["get", "post"])
    def blocked(self, request):
        if request.method == "GET":
            block = Block.objects.filter(block_from=request.user).select_related(
                "block_from", "block_to"
            )
            serializer = BlockSerializer(block, many=True)
            return Response(serializer.data)
        elif request.method == "POST":
            serializer = BlockSerializer(data=request.data)
            if serializer.is_valid():
                check = Block.objects.filter(
                    block_from=request.user,
                    block_to=serializer.validated_data["block_to"],
                )
                if check.exists():
                    check.delete()
                    return Response({"msg": "Unblocked"})
                else:
                    serializer.save(block_from=request.user)
                    Follower.objects.filter(
                        Q(
                            user_from=serializer.validated_data["block_to"],
                            user_to=request.user,
                        )
                        | Q(
                            user_from=request.user,
                            user_to=serializer.validated_data["block_to"],
                        )
                    ).delete()

                    return Response(serializer.data)
            return Response(serializer.errors)
