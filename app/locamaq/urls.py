from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import include, path, reverse_lazy

from crm.forms import FormLogin


class TrocarSenha(SuccessMessageMixin, auth_views.PasswordChangeView):
    template_name = "crm/senha.html"
    success_url = reverse_lazy("crm:inicio")
    success_message = "Senha alterada."

admin.site.site_header = "LocaMaq · administração"
admin.site.site_title = "LocaMaq"
admin.site.index_title = "Cadastros e usuários"

urlpatterns = [
    path(
        "entrar/",
        auth_views.LoginView.as_view(template_name="crm/login.html", authentication_form=FormLogin),
        name="login",
    ),
    path("sair/", auth_views.LogoutView.as_view(), name="logout"),
    path("senha/", TrocarSenha.as_view(), name="trocar_senha"),
    path("admin/", admin.site.urls),
    path("", include("crm.urls")),
]
