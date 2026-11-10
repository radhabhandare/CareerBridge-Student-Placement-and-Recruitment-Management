from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    ROLE=[('ADMIN','Admin'),('STUDENT','Student')]
    email=models.EmailField(unique=True)
    role=models.CharField(max_length=10,choices=ROLE,default='STUDENT')
    USERNAME_FIELD='email'
    REQUIRED_FIELDS=['username']

class StudentProfile(models.Model):
    STATES=[('PENDING','Pending'),('APPROVED','Approved'),('REJECTED','Rejected')]
    user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='student_profile')
    registration_number=models.CharField(max_length=40,unique=True)
    first_name=models.CharField(max_length=80)
    last_name=models.CharField(max_length=80,blank=True)
    phone=models.CharField(max_length=15)
    location=models.CharField(max_length=120)
    degree=models.CharField(max_length=100,blank=True)
    branch=models.CharField(max_length=100,blank=True)
    college=models.CharField(max_length=160,blank=True)
    passing_year=models.PositiveIntegerField(null=True,blank=True)
    cgpa=models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True)
    active_backlogs=models.PositiveIntegerField(default=0)
    skills=models.CharField(max_length=500,blank=True,help_text='Comma-separated skills')
    preferred_locations=models.CharField(max_length=300,blank=True)
    desired_roles=models.CharField(max_length=300,blank=True)
    resume=models.FileField(upload_to='resumes/',blank=True,null=True)
    approval_status=models.CharField(max_length=10,choices=STATES,default='PENDING')
    activated=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    def completion(self):
        checks=[bool(self.first_name and self.phone and self.location),bool(self.degree and self.branch and self.passing_year and self.cgpa is not None),bool(self.skills),bool(self.preferred_locations),bool(self.resume)]
        return round(sum(checks)*100/len(checks))
    def __str__(self): return f'{self.first_name} {self.last_name}'

class Education(models.Model):
    student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='education')
    qualification=models.CharField(max_length=80)
    institution=models.CharField(max_length=160)
    passing_year=models.PositiveIntegerField()
    score=models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    score_type=models.CharField(max_length=20,default='Percentage')

class Company(models.Model):
    name=models.CharField(max_length=160,unique=True)
    code=models.CharField(max_length=40,unique=True)
    industry=models.CharField(max_length=100,blank=True)
    location=models.CharField(max_length=120)
    email=models.EmailField(blank=True)
    website=models.URLField(blank=True)
    is_active=models.BooleanField(default=True)
    def __str__(self): return self.name

class Job(models.Model):
    company=models.ForeignKey(Company,on_delete=models.PROTECT,related_name='jobs')
    code=models.CharField(max_length=40,unique=True)
    title=models.CharField(max_length=160)
    location=models.CharField(max_length=120)
    package_lpa=models.DecimalField(max_digits=6,decimal_places=2,null=True,blank=True)
    qualification=models.CharField(max_length=120,blank=True)
    eligible_branches=models.CharField(max_length=250,blank=True,help_text='Comma separated; blank means all')
    min_cgpa=models.DecimalField(max_digits=4,decimal_places=2,null=True,blank=True)
    passing_year=models.PositiveIntegerField(null=True,blank=True)
    max_backlogs=models.PositiveIntegerField(default=0)
    required_skills=models.CharField(max_length=500,blank=True)
    description=models.TextField()
    deadline=models.DateField(null=True,blank=True)
    published=models.BooleanField(default=True)
    def __str__(self): return self.title

class JobApplication(models.Model):
    STATUS=[('APPLIED','Applied'),('REVIEWING','Reviewing'),('SHORTLISTED','Shortlisted'),('INTERVIEW','Interview'),('SELECTED','Selected'),('REJECTED','Rejected'),('WITHDRAWN','Withdrawn')]
    student=models.ForeignKey(StudentProfile,on_delete=models.CASCADE,related_name='applications')
    job=models.ForeignKey(Job,on_delete=models.PROTECT,related_name='applications')
    resume_copy=models.FileField(upload_to='application_resumes/')
    status=models.CharField(max_length=12,choices=STATUS,default='APPLIED')
    applied_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['student','job'],name='one_application_per_student_job')]

class LoginAttempt(models.Model):
    email=models.EmailField(unique=True)
    count=models.PositiveIntegerField(default=0)
    locked_until=models.DateTimeField(null=True,blank=True)
    def locked(self): return bool(self.locked_until and self.locked_until>timezone.now())

class Notification(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='notifications')
    message=models.CharField(max_length=300)
    created_at=models.DateTimeField(auto_now_add=True)
    read=models.BooleanField(default=False)
