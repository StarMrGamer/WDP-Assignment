from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, IntegerField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, NumberRange
from models import User, RegistrationCode

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
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
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
    photo = FileField('Photo', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    submit = SubmitField('Share Story')

class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=1)])
    submit = SubmitField('Send')
