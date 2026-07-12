from django.contrib import admin as django_admin
from django.contrib.auth.admin import UserAdmin
from users.models import Admin, CustomUser


@django_admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + ((
        'КорпМаркет',
        {
            'fields': ('photo', 'address', 'buyer_rating', 'seller_rating'),
        },
    ), )
    add_fieldsets = UserAdmin.add_fieldsets + ((
        'Данные сотрудника',
        {
            'fields': ('first_name', 'last_name', 'email', 'photo', 'address'),
        },
    ), )
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'buyer_rating',
        'seller_rating',
        'is_staff',
        'is_active',
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'address')


@django_admin.register(Admin)
class AdministratorAdmin(django_admin.ModelAdmin):
    list_display = ('user', )
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    list_select_related = ('user', )
