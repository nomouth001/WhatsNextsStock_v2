#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
초기 관리자 계정 생성 스크립트
"""

from app import create_app
from models import db, User

def create_admin_user():
    """초기 관리자 계정 생성"""
    app = create_app()
    
    with app.app_context():
        # 기존 관리자 계정 확인
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print("이미 관리자 계정이 존재합니다.")
            print(f"사용자명: {admin_user.username}")
            print(f"이메일: {admin_user.email}")
            return
        
        # 새 관리자 계정 생성
        admin = User(
            username='admin',
            email='admin@example.com',
            first_name='관리자',
            last_name='시스템',
            is_admin=True,
            is_verified=True,
            is_active=True
        )
        admin.set_password('admin123')  # 기본 비밀번호
        
        db.session.add(admin)
        db.session.commit()
        
        print("관리자 계정이 성공적으로 생성되었습니다!")
        print("사용자명: admin")
        print("비밀번호: admin123")
        print("이메일: admin@example.com")
        print("\n⚠️  보안을 위해 첫 로그인 후 비밀번호를 변경해주세요!")

if __name__ == '__main__':
    create_admin_user() 