from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from forms import LoginForm, RegistrationForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """로그인 페이지"""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.home'))
        else:
            return redirect(url_for('user.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user and user.check_password(form.password.data):
            if user.is_withdrawn:
                flash('탈퇴한 계정입니다.', 'error')
                return redirect(url_for('auth.login'))
            
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            
            if user.is_admin:
                return redirect(next_page) if next_page else redirect(url_for('admin.home'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('user.home'))
        else:
            flash('잘못된 사용자명 또는 비밀번호입니다.', 'error')
    
    return render_template('auth/login.html', title='로그인', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """회원가입 페이지"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash('회원가입이 완료되었습니다!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='회원가입', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """로그아웃"""
    logout_user()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('auth.login')) 