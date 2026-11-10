from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User,StudentProfile,Education,Company,Job,JobApplication,LoginAttempt,Notification
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets=UserAdmin.fieldsets+(('Placement role',{'fields':('role',)}),)
    add_fieldsets=UserAdmin.add_fieldsets+(('Extra',{'fields':('email','role')}),)
admin.site.register([StudentProfile,Education,Company,Job,JobApplication,LoginAttempt,Notification])
