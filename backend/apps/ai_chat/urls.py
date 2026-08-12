from django.urls import path

from apps.ai_chat.views import AIChatMessageListView, ConvertContentView, RefineContentView

app_name = "ai_chat"

urlpatterns = [
    path("messages/", AIChatMessageListView.as_view(), name="message-list"),
    path("refine/", RefineContentView.as_view(), name="refine"),
    path("convert/", ConvertContentView.as_view(), name="convert"),
]
