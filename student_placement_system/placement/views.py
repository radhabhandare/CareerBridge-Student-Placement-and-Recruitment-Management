from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_POST

from .models import *
from .forms import *
from .logic import eligibility


def admin_only(fn):
    return login_required(
        user_passes_test(
            lambda u: u.is_superuser or u.role == 'ADMIN'
        )(fn)
    )


def student_only(fn):
    def inner(request, *a, **kw):
        if not request.user.is_authenticated:
            return redirect('login')

        if request.user.role != 'STUDENT':
            return redirect('admin_home')

        p = getattr(request.user, 'student_profile', None)

        if not p or p.approval_status != 'APPROVED' or not p.activated:
            return render(
                request,
                'placement/pending.html',
                {'profile': p}
            )

        return fn(request, *a, **kw)

    return inner


# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

def home(request):
    return render(
        request,
        'placement/home.html',
        {
            'jobs': Job.objects.filter(published=True)[:6],
            'job_count': Job.objects.filter(published=True).count(),
            'company_count': Company.objects.filter(is_active=True).count()
        }
    )


# --------------------------------------------------
# STUDENT REGISTRATION
# --------------------------------------------------

def register(request):
    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data

        u = User.objects.create_user(
            username=d['email'],
            email=d['email'],
            password=d['password'],
            role='STUDENT',
            is_active=False
        )

        StudentProfile.objects.create(
            user=u,
            registration_number=d['registration_number'],
            first_name=d['first_name'],
            last_name=d['last_name'],
            phone=d['phone'],
            location=d['location']
        )

        messages.success(
            request,
            'Registration received. Wait for Admin approval.'
        )

        return redirect('success')

    return render(
        request,
        'placement/form.html',
        {
            'form': form,
            'heading': 'Student Registration',
            'button': 'Submit Registration'
        }
    )


def success(request):
    return render(request, 'placement/success.html')


# --------------------------------------------------
# STUDENT LOGIN
# --------------------------------------------------

def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        password = request.POST.get('password', '')

        attempt, _ = LoginAttempt.objects.get_or_create(email=email)

        if attempt.locked():
            messages.error(
                request,
                'Account login is temporarily locked for 30 minutes.'
            )

        else:
            u = authenticate(
                request,
                username=email,
                password=password
            )

            if not u:
                attempt.count += 1

                if attempt.count >= 3:
                    attempt.count = 0
                    attempt.locked_until = (
                        timezone.now() + timedelta(minutes=30)
                    )

                    messages.error(
                        request,
                        'Three failed attempts. Try again after 30 minutes.'
                    )
                else:
                    messages.error(
                        request,
                        f'Incorrect credentials. {3 - attempt.count} attempts remaining.'
                    )

                attempt.save()

            elif u.role == 'STUDENT' and (
                not hasattr(u, 'student_profile')
                or u.student_profile.approval_status != 'APPROVED'
                or not u.student_profile.activated
            ):
                messages.warning(
                    request,
                    'Your account is pending Admin approval or activation.'
                )

            else:
                attempt.count = 0
                attempt.locked_until = None
                attempt.save()

                login(request, u)

                if u.role == 'ADMIN' or u.is_superuser:
                    return redirect('admin_home')

                return redirect('dashboard')

    return render(request, 'placement/login.html')


# --------------------------------------------------
# STUDENT ACCOUNT ACTIVATION
# --------------------------------------------------

def activate(request, uid, token):
    try:
        user = User.objects.get(
            pk=force_str(urlsafe_base64_decode(uid))
        )
    except Exception:
        user = None

    if not user or not default_token_generator.check_token(user, token):
        messages.error(
            request,
            'Activation link is invalid or expired.'
        )
        return redirect('login')

    form = SetPasswordForm(user, request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()

        user.is_active = True
        user.save()

        p = user.student_profile
        p.activated = True
        p.save()

        messages.success(
            request,
            'Account activated. Login now.'
        )

        return redirect('login')

    return render(
        request,
        'placement/form.html',
        {
            'form': form,
            'heading': 'Set your password',
            'button': 'Activate account'
        }
    )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

def logout_page(request):
    logout(request)
    return redirect('home')


# --------------------------------------------------
# STUDENT DASHBOARD
# --------------------------------------------------

@login_required
def dashboard(request):
    if request.user.role == 'ADMIN' or request.user.is_superuser:
        return redirect('admin_home')

    p = request.user.student_profile

    return render(
        request,
        'placement/dashboard.html',
        {
            'p': p,
            'jobs': Job.objects.filter(published=True)[:5],
            'apps': p.applications.select_related('job')[:5]
        }
    )


# --------------------------------------------------
# STUDENT PROFILE
# --------------------------------------------------

@student_only
def profile(request):
    p = request.user.student_profile

    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=p
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated.')
        return redirect('profile')

    return render(
        request,
        'placement/form.html',
        {
            'form': form,
            'heading': 'My Profile',
            'button': 'Save Profile'
        }
    )


# --------------------------------------------------
# JOB LIST
# --------------------------------------------------

@student_only
def jobs(request):
    qs = Job.objects.filter(
        published=True,
        company__is_active=True
    ).select_related('company')

    q = request.GET.get('q', '')
    loc = request.GET.get('location', '')

    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(
            required_skills__icontains=q
        )

    if loc:
        qs = qs.filter(location__icontains=loc)

    return render(
        request,
        'placement/jobs.html',
        {
            'jobs': qs,
            'q': q,
            'location': loc
        }
    )


# --------------------------------------------------
# JOB DETAILS
# --------------------------------------------------

@student_only
def job_detail(request, pk):
    job = get_object_or_404(
        Job,
        pk=pk,
        published=True
    )

    result = eligibility(request.user.student_profile, job)

    applied = JobApplication.objects.filter(
        student=request.user.student_profile,
        job=job
    ).exists()

    return render(
        request,
        'placement/job_detail.html',
        {
            'job': job,
            'result': result,
            'applied': applied
        }
    )


# --------------------------------------------------
# APPLY FOR JOB
# --------------------------------------------------

@student_only
@require_POST
def apply(request, pk):
    job = get_object_or_404(
        Job,
        pk=pk,
        published=True
    )

    p = request.user.student_profile
    result = eligibility(p, job)

    if not result['eligible']:
        messages.error(
            request,
            'Not eligible: ' + ' '.join(result['reasons'])
        )
        return redirect('job_detail', pk=pk)

    if not p.resume:
        messages.error(
            request,
            'Upload your resume before applying.'
        )
        return redirect('profile')

    try:
        JobApplication.objects.create(
            student=p,
            job=job,
            resume_copy=p.resume.name
        )

    except IntegrityError:
        messages.error(
            request,
            'Duplicate application prevented.'
        )

    else:
        Notification.objects.create(
            user=request.user,
            message=f'Application submitted for {job.title}.'
        )

        messages.success(
            request,
            'Application submitted.'
        )

    return redirect('applications')


# --------------------------------------------------
# STUDENT APPLICATIONS
# --------------------------------------------------

@student_only
def applications(request):
    return render(
        request,
        'placement/applications.html',
        {
            'apps': request.user.student_profile.applications.select_related(
                'job',
                'job__company'
            )
        }
    )


# --------------------------------------------------
# STUDENT NOTIFICATIONS
# --------------------------------------------------

@student_only
def notices(request):
    items = request.user.notifications.all()
    items.update(read=True)

    return render(
        request,
        'placement/notices.html',
        {'items': items}
    )


# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------

@admin_only
def admin_home(request):
    return render(
        request,
        'placement/admin_home.html',
        {
            'students': StudentProfile.objects.count(),
            'pending': StudentProfile.objects.filter(
                approval_status='PENDING'
            ).count(),
            'companies': Company.objects.count(),
            'jobs': Job.objects.filter(published=True).count(),
            'applications': JobApplication.objects.count(),
            'selected': JobApplication.objects.filter(
                status='SELECTED'
            ).count()
        }
    )


# --------------------------------------------------
# ADMIN: STUDENT LIST
# --------------------------------------------------

@admin_only
def admin_students(request):
    status = request.GET.get('status', '')

    qs = StudentProfile.objects.select_related('user')

    if status in ('PENDING', 'APPROVED', 'REJECTED'):
        qs = qs.filter(approval_status=status)

    return render(
        request,
        'placement/admin_students.html',
        {'students': qs}
    )


# --------------------------------------------------
# SEND STUDENT ACTIVATION EMAIL
# --------------------------------------------------

def send_student_activation_email(request, student_profile):
    user = student_profile.user

    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    link = request.build_absolute_uri(
        reverse('activate', args=[uid, token])
    )

    send_mail(
        'CareerBridge - Student Account Activation',
        (
            f'Hello {student_profile.first_name},\n\n'
            'Your CareerBridge registration has been approved.\n'
            f'Your login email is: {user.email}\n\n'
            'Please click the link below to set your password:\n'
            f'{link}\n\n'
            'If you did not request this account, please ignore this email.'
        ),
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )


# --------------------------------------------------
# ADMIN: APPROVE STUDENT
# --------------------------------------------------

@admin_only
@require_POST
def approve(request, pk):
    p = get_object_or_404(StudentProfile, pk=pk)

    p.approval_status = 'APPROVED'
    p.save()

    # Do not send another activation email to an activated account.
    if p.activated or p.user.is_active:
        messages.info(
            request,
            'Student is already activated. No activation email was sent.'
        )
        return redirect('admin_students')

    try:
        send_student_activation_email(request, p)

        messages.success(
            request,
            f'Approved. Activation email sent to {p.user.email}.'
        )

    except Exception as e:
        messages.error(
            request,
            f'Student approved, but email could not be sent: {e}'
        )

    return redirect('admin_students')


# --------------------------------------------------
# ADMIN: RESEND ACTIVATION EMAIL
# --------------------------------------------------

@admin_only
@require_POST
def resend_activation(request, pk):
    p = get_object_or_404(StudentProfile, pk=pk)

    if p.approval_status != 'APPROVED':
        messages.error(
            request,
            'Approve this student before sending an activation email.'
        )
        return redirect('admin_students')

    if p.activated or p.user.is_active:
        messages.warning(
            request,
            'This student account is already activated. No new email was sent.'
        )
        return redirect('admin_students')

    try:
        send_student_activation_email(request, p)

        messages.success(
            request,
            f'Activation email resent successfully to {p.user.email}.'
        )

    except Exception as e:
        messages.error(
            request,
            f'Email could not be sent: {e}'
        )

    return redirect('admin_students')


# --------------------------------------------------
# ADMIN: REJECT STUDENT
# --------------------------------------------------

@admin_only
@require_POST
def reject(request, pk):
    p = get_object_or_404(StudentProfile, pk=pk)

    p.approval_status = 'REJECTED'
    p.save()

    messages.info(request, 'Student rejected.')

    return redirect('admin_students')


# --------------------------------------------------
# ADMIN: COMPANY MANAGEMENT
# --------------------------------------------------

@admin_only
def companies(request):
    form = CompanyForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('companies')

    return render(
        request,
        'placement/companies.html',
        {
            'form': form,
            'companies': Company.objects.all()
        }
    )


# --------------------------------------------------
# ADMIN: JOB MANAGEMENT
# --------------------------------------------------

@admin_only
def jobs_admin(request):
    form = JobForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('jobs_admin')

    return render(
        request,
        'placement/jobs_admin.html',
        {
            'form': form,
            'jobs': Job.objects.select_related('company')
        }
    )


# --------------------------------------------------
# ADMIN: APPLICATION MANAGEMENT
# --------------------------------------------------

@admin_only
def apps_admin(request):
    if request.method == 'POST':
        app = get_object_or_404(
            JobApplication,
            pk=request.POST.get('app_id')
        )

        status = request.POST.get('status')

        if status in dict(JobApplication.STATUS):
            app.status = status
            app.save()

            Notification.objects.create(
                user=app.student.user,
                message=f'Your {app.job.title} application status is now {status}.'
            )

            messages.success(
                request,
                'Application updated.'
            )

        return redirect('apps_admin')

    return render(
        request,
        'placement/apps_admin.html',
        {
            'apps': JobApplication.objects.select_related(
                'student',
                'job',
                'job__company'
            )
        }
    )