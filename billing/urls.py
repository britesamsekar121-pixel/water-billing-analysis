from django.urls import path
from . import views

urlpatterns = [
    path("", views.login, name="login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("add/", views.add_customer, name="add"),
    path("view/", views.view_customers, name="view"),
    path("bill/<str:cid>/", views.download_bill, name="bill"),
    path("user/<cid>/", views.user_view, name="user"),
    path("delete/<cid>/", views.delete_customer),
    path("edit/<cid>/", views.edit_customer, name="edit"),
    path("pay/<cid>/", views.pay_bill),
    
]
