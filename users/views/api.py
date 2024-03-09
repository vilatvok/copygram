from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Subquery, OuterRef
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import status, filters
from rest_framework.pagination import PageNumberPagination

from common.utils import get_posts, create_action

from users.serializers import (
    ActionSerializer, 
    UserCreateSerializer, 
    UserSerializer, 
    PasswordSerializer,
    ActivitySerializer
)
from users.permissions.api import IsOwner
from users.models import Action, Follower, Block
from users.utils import Recommender, set_blocked

from mainsite.models import Comment, PostMedia, Story
from mainsite.serializers import (
    StorySerializer, 
    PostListSerializer, 
    CommentSerializer
)

User = get_user_model()


class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserViewSet(ModelViewSet):
    permission_classes = [IsOwner]
    lookup_field = 'slug'
    pagination_class = UserPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['username']
    search_fields = ['username']

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return User.objects.exclude(id__in=self.request.session['blocked']).annotate(
                followers_count=Count('user_to', distinct=True),
                following_count=Count('user_from', distinct=True)
            )
        return User.objects.annotate(
            followers_count=Count('user_to', distinct=True), 
            following_count=Count('user_from', distinct=True)
        ).all()
    
    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return UserCreateSerializer
        return UserSerializer

    @action(detail=True, methods=['patch'], url_path='pswd')
    def change_pswd(self, request, slug=None):
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = self.get_object()
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response({'status': 'Changed'})
        return Response({'status': "Isn't changed"}, status.HTTP_400_BAD_REQUEST)

    @action(detail=True)
    def actions(self, request, slug=None):
        user = self.get_object()
        actions = Action.objects.filter(
            Q(post__owner=user) |
            Q(user=user)
        ).select_related('owner', 'content_type')
        serializer = ActionSerializer(actions, many=True)
        return Response(serializer.data)

    @action(
        detail=True, 
        methods=['get', 'delete'], 
        url_path='action/(?P<action_id>[^/.]+)'
    )
    def get_action(self, request, action_id, slug=None):
        user = self.get_object()
        exist = Action.objects.filter(Q(post__owner=user) | Q(user=user), id=action_id)
        if not exist:
            return Response({'status': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        if request.method == 'GET':
            serializer = ActionSerializer(exist.first())
            return Response(serializer.data)
        exist.delete()
        return Response({'status': 'deleted'}, status.HTTP_204_NO_CONTENT)

    @action(detail=True)
    def posts(self, request, slug=None):
        post = get_posts(self.get_object())
        serializer = PostListSerializer(post, context={'request': request}, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def stories(self, request, slug=None):
        story = (
            Story.objects.filter(owner=self.get_object()).
            exclude(owner__in=request.session['blocked']).
            select_related('owner')
        )
        serializer = StorySerializer(story, many=True)
        return Response(serializer.data)

    @action(detail=True)
    def followers(self, request, slug=None):
        followers = (
            User.objects.exclude(id__in=request.session['blocked']).
            annotate(
                followers_count=Count('user_to', distinct=True),
                following_count=Count('user_from', distinct=True)
            ).filter(user_from__user_to=self.get_object())
        )
        serializer = UserSerializer(
            followers, 
            many=True, 
            context={'request': request}, 
            fields=('phone', 'last_login'),
        )
        return Response(serializer.data)

    @action(detail=True)
    def following(self, request, slug=None):
        following = (
            User.objects.exclude(id__in=request.session['blocked']).
            annotate(
                followers_count=Count('user_to', distinct=True),
                following_count=Count('user_from', distinct=True)
            ).filter(user_to__user_from=self.get_object())
        )
        serializer = UserSerializer(
            following, 
            many=True, 
            context={'request': request}, 
            fields=('phone', 'last_login')
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def follow(self, request, slug=None):
        """
        Is used for following another user.
        Creates recommendations, base on user's followers.
        If the user has been already followed to another user then
        cancel this following and delete user's followers from recommendations.
        """
        user = request.user
        user_to = self.get_object()
        if user == user_to:
            return Response(
                {'status': 'You cant follow to yourself'}, 
                status.HTTP_403_FORBIDDEN
            )

        is_followed = Follower.objects.filter(user_from=user, user_to=user_to)
        others = User.objects.exclude(id=user.id).filter(user_to__user_from=user_to)
        r = Recommender()
        if is_followed.exists():
            is_followed.delete()
            r.add_suggestions(user, [user_to])
            r.remove_suggestions(user, others)
            return Response({'status': 'Unfollowed'})
        else:
            Follower.objects.create(user_from=user, user_to=user_to)
            r.add_suggestions(user, others)
            r.remove_suggestions(user, [user_to])
            user_following = User.objects.filter(user_to__user_from=user)
            user_followers = User.objects.filter(user_from__user_to=user)
            for _ in user_followers:
                r.add_suggestions(_, user_following)
            create_action(user, 'following you', target=user_to)
            return Response({'status': 'Followed'})

    @action(detail=True)
    def recommendations(self, request, slug=None):
        r = Recommender()
        rec = r.suggests_for_user(self.get_object())
        serializers = UserSerializer(rec, many=True, context={'request': request})
        return Response(serializers.data)

    @action(detail=True)
    def blocked(self, request, slug=None):
        block = User.objects.filter(
            block_to__block_from=self.get_object()
        )
        serializer = UserSerializer(
            block,
            many=True, 
            context={'request': request}, 
            fields=('phone', 'username', 'last_login')
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def block(self, request, slug=None):
        """
        Block the user and delete all connections between users.
        Otherwise, unblock the user.
        """
        user = request.user
        user_to = self.get_object()
        if user == user_to:
            return Response(
                {'status': 'You cant block yourself'}, 
                status.HTTP_403_FORBIDDEN
            )
        
        check = Block.objects.filter(block_from=user, block_to=user_to)
        if check.exists():
            check.delete()
            set_blocked(user, request)
            return Response({'status': 'Unblocked'}, status.HTTP_204_NO_CONTENT)
        else:
            Block.objects.create(block_from=user, block_to=user_to)
            posts = user.like.filter(owner=user_to)
            user_posts = user_to.like.filter(owner=user)
            for post in posts:
                post.is_like.remove(user)
                post.save()
            for post in user_posts:
                post.is_like.remove(user_to)
                post.save()
            Comment.objects.filter(
                Q(owner=user_to, post__owner=user) | 
                Q(owner=user, post__owner=user_to)
            ).delete()
            Follower.objects.filter(
                Q(user_from=user_to, user_to=user) | 
                Q(user_from=user, user_to=user_to)
            ).delete()
            Action.objects.filter(
                Q(owner=user_to, post__owner=user) |
                Q(owner=user_to, user=user) |
                Q(owner=user, post__owner=user_to) |
                Q(owner=user, user=user_to)
            ).delete()
            set_blocked(user, request)
            return Response({'status': 'Blocked'})
    
    @action(detail=True)
    def activity(self, request, slug=None):
        user = self.get_object()
        subquery = PostMedia.objects.filter(
            post=OuterRef('pk')
        ).values('file')[:1]
        posts = (
            user.like.annotate(file=Subquery(subquery)).
            select_related('owner').prefetch_related('tags')
        )
        serializer = ActivitySerializer(
            posts,
            many=True, 
            context={'request': request}
        )
        comments = user.comment_owner.all()
        comments_serializer = CommentSerializer(
            comments, 
            many=True, 
            fields=('text', 'date')
        )
        response_data = {}
        response_data['posts'] = serializer.data
        response_data['comments'] = comments_serializer.data
        return Response(response_data)