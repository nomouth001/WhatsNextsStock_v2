from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    """로그인 폼"""
    username = StringField('사용자명', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('비밀번호', validators=[DataRequired()])
    remember_me = BooleanField('로그인 상태 유지')
    submit = SubmitField('로그인')

class RegistrationForm(FlaskForm):
    """회원가입 폼"""
    username = StringField('사용자명', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('이메일', validators=[DataRequired(), Email()])
    first_name = StringField('이름', validators=[Length(max=50)])
    last_name = StringField('성', validators=[Length(max=50)])
    password = PasswordField('비밀번호', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('비밀번호 확인', 
                             validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('회원가입')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('이미 사용 중인 사용자명입니다.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('이미 등록된 이메일 주소입니다.')

class CSVUploadForm(FlaskForm):
    """CSV 업로드 폼"""
    market_type = SelectField('시장 구분', 
                             choices=[('KOSPI', 'KOSPI'), ('KOSDAQ', 'KOSDAQ'), ('US', '미국 주식')],
                             validators=[DataRequired()])
    csv_file = FileField('CSV 파일', 
                        validators=[DataRequired(), 
                                  FileAllowed(['csv'], 'CSV 파일만 업로드 가능합니다.')])
    description = TextAreaField('설명')
    submit = SubmitField('업로드')

class StockListForm(FlaskForm):
    """주식 리스트 생성/수정 폼"""
    name = StringField('리스트명', validators=[DataRequired(), Length(max=100)])
    market_type = SelectField('시장 구분', 
                             choices=[('KOSPI', 'KOSPI'), ('KOSDAQ', 'KOSDAQ'), ('US', '미국 주식')],
                             validators=[DataRequired()])
    description = TextAreaField('설명')
    submit = SubmitField('저장') 