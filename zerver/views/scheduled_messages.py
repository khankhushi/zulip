from typing import List, TypedDict

from django.http import HttpRequest, HttpResponse

from zerver.actions.scheduled_messages import delete_scheduled_message
from zerver.lib.request import has_request_variables
from zerver.lib.response import json_success
from zerver.models import ScheduledMessage, UserProfile, get_recipient_ids


class ScheduledMessageDict(TypedDict):
    scheduled_message_id: int
    to: List[int]
    type: str
    content: str
    rendered_content: str
    topic: str
    deliver_at: int


@has_request_variables
def fetch_scheduled_messages(request: HttpRequest, user_profile: UserProfile) -> HttpResponse:
    scheduled_messages = ScheduledMessage.objects.filter(
        sender=user_profile, delivered=False, delivery_type=ScheduledMessage.SEND_LATER
    ).order_by("scheduled_timestamp")
    scheduled_message_dicts: List[ScheduledMessageDict] = []

    for scheduled_message in scheduled_messages:
        recipient, recipient_type_str = get_recipient_ids(
            scheduled_message.recipient, user_profile.id
        )

        msg_to_dict: ScheduledMessageDict = {
            "scheduled_message_id": scheduled_message.id,
            "to": recipient,
            "type": recipient_type_str,
            "content": scheduled_message.content,
            "rendered_content": scheduled_message.rendered_content,
            "topic": scheduled_message.topic_name(),
            "deliver_at": int(scheduled_message.scheduled_timestamp.timestamp() * 1000),
        }
        scheduled_message_dicts.append(msg_to_dict)

    return json_success(request, data={"scheduled_messages": scheduled_message_dicts})


@has_request_variables
def delete_scheduled_messages(
    request: HttpRequest, user_profile: UserProfile, scheduled_message_id: int
) -> HttpResponse:
    delete_scheduled_message(user_profile, scheduled_message_id)
    return json_success(request)
