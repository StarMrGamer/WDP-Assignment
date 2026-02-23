import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange, Optional
from models import User, RegistrationCode


def validate_password_strength(form, field):
    """
    Custom validator for password strength.
    Requires: min 8 chars, 1 uppercase, 1 lowercase, 1 number.
    """
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=13, max=120)])
    role = SelectField('Role', choices=[('senior', 'Senior'), ('youth', 'Youth')], validators=[DataRequired()])
    registration_code = StringField('Registration Code', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please login instead.')

    def validate_registration_code(self, registration_code):
        code = RegistrationCode.query.filter_by(code=registration_code.data, is_used=False).first()
        if not code:
            raise ValidationError('Invalid or already used registration code.')

    def validate_age(self, age):
        if self.role.data == 'senior' and age.data < 60:
            raise ValidationError('Seniors must be 60 years or older.')
        if self.role.data == 'youth' and age.data < 13:
            raise ValidationError('Youth volunteers must be 13 years or older.')
        if self.role.data == 'youth' and age.data >= 60:
            raise ValidationError('If you are 60 or older, please register as a Senior.')

    def validate_phone(self, phone):
        # Singapore phone validation: 8 digits, starts with 6, 8, or 9
        import re
        if not re.match(r'^[689]\d{7}$', phone.data):
            raise ValidationError('Please enter a valid Singapore phone number (8 digits, starting with 6, 8, or 9).')

class GoogleCompleteForm(FlaskForm):
    """Form for completing registration after Google Sign-In."""
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    phone = StringField('Phone', validators=[DataRequired()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=13, max=120)])
    registration_code = StringField('Registration Code', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Complete Registration')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_registration_code(self, registration_code):
        code = RegistrationCode.query.filter_by(code=registration_code.data, is_used=False).first()
        if not code:
            raise ValidationError('Invalid or already used registration code.')

    def validate_phone(self, phone):
        import re
        if not re.match(r'^[689]\d{7}$', phone.data):
            raise ValidationError('Please enter a valid Singapore phone number (8 digits, starting with 6, 8, or 9).')


class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    school = StringField('School')
    bio = TextAreaField('Bio')
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=13, max=120)])
    profile_picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')])
    submit = SubmitField('Update Profile')

    def validate_phone(self, phone):
        import re
        if not re.match(r'^[689]\d{7}$', phone.data):
            raise ValidationError('Please enter a valid Singapore phone number (8 digits, starting with 6, 8, or 9).')

class StoryForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=200)])
    content = TextAreaField('Story Content', validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('Childhood', 'Childhood'), 
        ('Work Life', 'Work Life'), 
        ('Family', 'Family'), 
        ('Hobbies', 'Hobbies'), 
        ('Other', 'Other')
    ], validators=[DataRequired()])
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'webp', 'heic', 'bmp', 'mp4', 'mov', 'avi', 'webm', 'mkv'])])
    submit = SubmitField('Share Story')

class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('Send')


class SupportTicketForm(FlaskForm):
    guest_email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    ticket_type = SelectField('Issue Type', choices=[
        ('Bug Report', 'Bug Report'),
        ('Feature Request', 'Feature Request'),
        ('Account Issue', 'Account Issue'),
        ('General Inquiry', 'General Inquiry')
    ], validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10, max=1000)])
    submit = SubmitField('Submit Ticket')
