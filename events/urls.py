from django.urls import path
from .views import (
    EventListView, EventCreateView, EventDetailView, EventRemoveReminderView, EventReminderView,
    EventEditView, EventDeleteView
)

app_name = 'events'

urlpatterns = [
    path('', EventListView.as_view(), name='event_list'),
    path('create/', EventCreateView.as_view(), name='event_create'),
    path('<uuid:id>/', EventDetailView.as_view(), name='event_detail'),
    path('<uuid:id>/edit/', EventEditView.as_view(), name='event_edit'),
    path('<uuid:id>/delete/', EventDeleteView.as_view(), name='event_delete'),

    path('<uuid:id>/remind/', EventReminderView.as_view(), name='event_reminder'),
    path('<uuid:id>/remind/cancel/', EventRemoveReminderView.as_view(), name='event_reminder_cancel'),
]
