from django.db.models import Manager, OuterRef, Subquery


class ChatManager(Manager):
    def annotated(self):
        from chats.models import Message
        
        chat_id = OuterRef('pk')
        msg = Message.objects.filter(object_id=chat_id).order_by('-timestamp')

        # Annotate objects with the last message
        qs = self.annotate(
            last_message=Subquery(msg.values('content')[:1]),
            last_message_user=Subquery(msg.values('user__username')[:1]),
            last_message_time=Subquery(msg.values('timestamp')[:1]),
        )
        return qs
