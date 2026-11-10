from django import forms
from django.contrib.auth.password_validation import validate_password
from .models import StudentProfile,Company,Job,User
class RegisterForm(forms.Form):
    email=forms.EmailField()
    registration_number=forms.CharField(max_length=40)
    first_name=forms.CharField(max_length=80)
    last_name=forms.CharField(max_length=80,required=False)
    phone=forms.CharField(max_length=15)
    location=forms.CharField(max_length=120)
    password=forms.CharField(widget=forms.PasswordInput)
    confirm_password=forms.CharField(widget=forms.PasswordInput)
    def clean_email(self):
        v=self.cleaned_data['email'].lower()
        if User.objects.filter(email=v).exists(): raise forms.ValidationError('Email already registered.')
        return v
    def clean_registration_number(self):
        from .models import StudentProfile
        v=self.cleaned_data['registration_number'].upper().strip()
        if StudentProfile.objects.filter(registration_number=v).exists(): raise forms.ValidationError('Registration number already exists.')
        return v
    def clean(self):
        d=super().clean()
        if d.get('password') and d.get('confirm_password') and d['password']!=d['confirm_password']: self.add_error('confirm_password','Passwords do not match.')
        if d.get('password'):
            try: validate_password(d['password'])
            except forms.ValidationError as e: self.add_error('password',e)
        return d
class ProfileForm(forms.ModelForm):
    class Meta:
        model=StudentProfile
        exclude=['user','registration_number','approval_status','activated','created_at']
        widgets={'resume':forms.ClearableFileInput(attrs={'accept':'.pdf,.docx'})}
    def clean_resume(self):
        f=self.cleaned_data.get('resume')
        if f:
            if f.size>5*1024*1024: raise forms.ValidationError('Maximum resume size is 5 MB.')
            ext=f.name.rsplit('.',1)[-1].lower()
            head=f.read(8); f.seek(0)
            if ext=='pdf' and not head.startswith(b'%PDF'): raise forms.ValidationError('Invalid PDF file.')
            if ext=='docx' and not head.startswith(b'PK'): raise forms.ValidationError('Invalid DOCX file.')
            if ext not in ('pdf','docx'): raise forms.ValidationError('Only PDF and DOCX are allowed.')
        return f
class CompanyForm(forms.ModelForm):
    class Meta: model=Company; fields='__all__'
class JobForm(forms.ModelForm):
    class Meta:
        model=Job; exclude=[]
        widgets={'deadline':forms.DateInput(attrs={'type':'date'})}
