"""
Phase 5: 프로덕션 환경 설정 스크립트
프로덕션 환경에 필요한 모든 설정을 자동화합니다.
"""

import os
import sys
import shutil
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionEnvironmentSetup:
    """프로덕션 환경 설정 클래스"""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.setup_results = {}
        
    def setup_environment(self) -> Dict[str, Any]:
        """환경 설정 실행"""
        logger.info("🏭 프로덕션 환경 설정 시작")
        
        try:
            # 1. 시스템 요구사항 확인
            logger.info("🔍 1단계: 시스템 요구사항 확인")
            system_check = self._check_system_requirements()
            
            # 2. 의존성 설치
            logger.info("📦 2단계: 의존성 설치")
            dependency_check = self._install_dependencies()
            
            # 3. 환경 변수 설정
            logger.info("⚙️ 3단계: 환경 변수 설정")
            env_check = self._setup_environment_variables()
            
            # 4. 로그 디렉토리 생성
            logger.info("📝 4단계: 로그 디렉토리 생성")
            log_check = self._setup_logging_directories()
            
            # 5. 캐시 디렉토리 설정
            logger.info("💾 5단계: 캐시 디렉토리 설정")
            cache_check = self._setup_cache_directories()
            
            # 6. 데이터베이스 설정
            logger.info("🗄️ 6단계: 데이터베이스 설정")
            db_check = self._setup_database()
            
            # 7. 보안 설정
            logger.info("🔒 7단계: 보안 설정")
            security_check = self._setup_security()
            
            # 결과 통합
            self.setup_results = {
                "system_requirements": system_check,
                "dependencies": dependency_check,
                "environment_variables": env_check,
                "logging_directories": log_check,
                "cache_directories": cache_check,
                "database": db_check,
                "security": security_check,
                "timestamp": datetime.now().isoformat()
            }
            
            # 전체 성공 여부 확인
            all_success = all(
                result.get("success", False) 
                for result in self.setup_results.values() 
                if isinstance(result, dict)
            )
            
            self.setup_results["overall_success"] = all_success
            
            if all_success:
                logger.info("✅ 프로덕션 환경 설정 완료")
            else:
                logger.warning("⚠️ 일부 설정이 실패했습니다")
            
            return self.setup_results
            
        except Exception as e:
            logger.error(f"❌ 프로덕션 환경 설정 실패 - {str(e)}")
            return {"error": str(e), "success": False}
    
    def _check_system_requirements(self) -> Dict[str, Any]:
        """시스템 요구사항 확인"""
        try:
            requirements = {
                "python_version": self._check_python_version(),
                "memory_available": self._check_memory_availability(),
                "disk_space": self._check_disk_space(),
                "network_connectivity": self._check_network_connectivity(),
                "required_directories": self._check_required_directories()
            }
            
            # 전체 성공 여부 확인
            all_passed = all(requirements.values())
            
            return {
                "success": all_passed,
                "requirements": requirements,
                "passed_count": sum(requirements.values()),
                "total_count": len(requirements)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _check_python_version(self) -> bool:
        """Python 버전 확인"""
        try:
            version = sys.version_info
            required_version = (3, 8)
            
            if version >= required_version:
                logger.info(f"✅ Python 버전 확인: {version.major}.{version.minor}.{version.micro}")
                return True
            else:
                logger.error(f"❌ Python 버전 부족: {version.major}.{version.minor}.{version.micro} (필요: {required_version[0]}.{required_version[1]}+)")
                return False
                
        except Exception as e:
            logger.error(f"❌ Python 버전 확인 실패: {str(e)}")
            return False
    
    def _check_memory_availability(self) -> bool:
        """메모리 가용성 확인"""
        try:
            import psutil
            
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            required_gb = 2.0  # 최소 2GB 필요
            
            if available_gb >= required_gb:
                logger.info(f"✅ 메모리 확인: {available_gb:.2f}GB 사용 가능")
                return True
            else:
                logger.error(f"❌ 메모리 부족: {available_gb:.2f}GB (필요: {required_gb}GB+)")
                return False
                
        except Exception as e:
            logger.error(f"❌ 메모리 확인 실패: {str(e)}")
            return False
    
    def _check_disk_space(self) -> bool:
        """디스크 공간 확인"""
        try:
            import psutil
            
            disk = psutil.disk_usage('/')
            available_gb = disk.free / (1024**3)
            required_gb = 5.0  # 최소 5GB 필요
            
            if available_gb >= required_gb:
                logger.info(f"✅ 디스크 공간 확인: {available_gb:.2f}GB 사용 가능")
                return True
            else:
                logger.error(f"❌ 디스크 공간 부족: {available_gb:.2f}GB (필요: {required_gb}GB+)")
                return False
                
        except Exception as e:
            logger.error(f"❌ 디스크 공간 확인 실패: {str(e)}")
            return False
    
    def _check_network_connectivity(self) -> bool:
        """네트워크 연결 확인"""
        try:
            import urllib.request
            
            # 인터넷 연결 확인
            urllib.request.urlopen('http://www.google.com', timeout=5)
            logger.info("✅ 네트워크 연결 확인")
            return True
            
        except Exception as e:
            logger.error(f"❌ 네트워크 연결 확인 실패: {str(e)}")
            return False
    
    def _check_required_directories(self) -> bool:
        """필요한 디렉토리 확인"""
        try:
            required_dirs = [
                'services',
                'static',
                'templates',
                'routes',
                'logs',
                'uploads',
                'z_archives'
            ]
            
            missing_dirs = []
            for dir_name in required_dirs:
                dir_path = os.path.join(self.project_root, dir_name)
                if not os.path.exists(dir_path):
                    missing_dirs.append(dir_name)
            
            if not missing_dirs:
                logger.info("✅ 필요한 디렉토리 확인")
                return True
            else:
                logger.error(f"❌ 누락된 디렉토리: {missing_dirs}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 디렉토리 확인 실패: {str(e)}")
            return False
    
    def _install_dependencies(self) -> Dict[str, Any]:
        """의존성 설치"""
        try:
            # requirements.txt 확인
            requirements_file = os.path.join(self.project_root, 'requirements.txt')
            if not os.path.exists(requirements_file):
                return {"success": False, "error": "requirements.txt 파일이 없습니다"}
            
            # pip 업그레이드
            logger.info("📦 pip 업그레이드 중...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                         check=True, capture_output=True)
            
            # 의존성 설치
            logger.info("📦 의존성 설치 중...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', requirements_file], 
                                  check=True, capture_output=True, text=True)
            
            # 설치된 패키지 확인
            installed_packages = self._get_installed_packages()
            
            return {
                "success": True,
                "installed_packages": installed_packages,
                "installation_output": result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"의존성 설치 실패: {e.stderr}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_installed_packages(self) -> List[str]:
        """설치된 패키지 목록 가져오기"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                                  check=True, capture_output=True, text=True)
            
            packages = []
            for line in result.stdout.split('\n')[2:]:  # 헤더 제외
                if line.strip():
                    package_name = line.split()[0]
                    packages.append(package_name)
            
            return packages
            
        except Exception as e:
            logger.warning(f"패키지 목록 가져오기 실패: {str(e)}")
            return []
    
    def _setup_environment_variables(self) -> Dict[str, Any]:
        """환경 변수 설정"""
        try:
            env_vars = {
                'FLASK_ENV': 'production',
                'FLASK_DEBUG': 'False',
                'SECRET_KEY': self._generate_secret_key(),
                'DATABASE_URL': 'sqlite:///production.db',
                'CACHE_TYPE': 'filesystem',
                'CACHE_DIR': os.path.join(self.project_root, 'cache'),
                'LOG_LEVEL': 'INFO',
                'LOG_FILE': os.path.join(self.project_root, 'logs', 'production.log'),
                'UPLOAD_FOLDER': os.path.join(self.project_root, 'uploads'),
                'MAX_CONTENT_LENGTH': '16777216'  # 16MB
            }
            
            # .env 파일 생성
            env_file_path = os.path.join(self.project_root, '.env')
            with open(env_file_path, 'w', encoding='utf-8') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
            
            logger.info("✅ 환경 변수 설정 완료")
            
            return {
                "success": True,
                "env_file_path": env_file_path,
                "variables_count": len(env_vars)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_secret_key(self) -> str:
        """시크릿 키 생성"""
        import secrets
        return secrets.token_hex(32)
    
    def _setup_logging_directories(self) -> Dict[str, Any]:
        """로깅 디렉토리 설정"""
        try:
            log_dirs = [
                'logs',
                'logs/analysis',
                'logs/errors',
                'logs/performance',
                'logs/access'
            ]
            
            created_dirs = []
            for log_dir in log_dirs:
                dir_path = os.path.join(self.project_root, log_dir)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                    created_dirs.append(log_dir)
            
            # 로그 파일 생성
            log_files = [
                'logs/production.log',
                'logs/error.log',
                'logs/performance.log',
                'logs/access.log'
            ]
            
            for log_file in log_files:
                file_path = os.path.join(self.project_root, log_file)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {log_file} - 생성일: {datetime.now().isoformat()}\n")
            
            logger.info("✅ 로깅 디렉토리 설정 완료")
            
            return {
                "success": True,
                "created_directories": created_dirs,
                "log_files": log_files
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _setup_cache_directories(self) -> Dict[str, Any]:
        """캐시 디렉토리 설정"""
        try:
            cache_dirs = [
                'cache',
                'cache/data',
                'cache/charts',
                'cache/analysis',
                'cache/temp'
            ]
            
            created_dirs = []
            for cache_dir in cache_dirs:
                dir_path = os.path.join(self.project_root, cache_dir)
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path)
                    created_dirs.append(cache_dir)
            
            # 캐시 정리 스크립트 생성
            cache_cleanup_script = os.path.join(self.project_root, 'scripts', 'cleanup_cache.py')
            if not os.path.exists(cache_cleanup_script):
                with open(cache_cleanup_script, 'w', encoding='utf-8') as f:
                    f.write(self._get_cache_cleanup_script())
            
            logger.info("✅ 캐시 디렉토리 설정 완료")
            
            return {
                "success": True,
                "created_directories": created_dirs,
                "cache_cleanup_script": cache_cleanup_script
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_cache_cleanup_script(self) -> str:
        """캐시 정리 스크립트 내용"""
        return '''"""
캐시 정리 스크립트
오래된 캐시 파일들을 정리합니다.
"""

import os
import time
import shutil
from datetime import datetime, timedelta

def cleanup_cache():
    """캐시 정리"""
    cache_dir = "cache"
    max_age_hours = 24  # 24시간 이상 된 파일 삭제
    
    if not os.path.exists(cache_dir):
        return
    
    current_time = time.time()
    deleted_files = 0
    
    for root, dirs, files in os.walk(cache_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_age = current_time - os.path.getmtime(file_path)
            
            if file_age > (max_age_hours * 3600):
                try:
                    os.remove(file_path)
                    deleted_files += 1
                except Exception as e:
                    print(f"파일 삭제 실패: {file_path} - {e}")
    
    print(f"캐시 정리 완료: {deleted_files}개 파일 삭제")

if __name__ == "__main__":
    cleanup_cache()
'''
    
    def _setup_database(self) -> Dict[str, Any]:
        """데이터베이스 설정"""
        try:
            # SQLite 데이터베이스 초기화
            db_path = os.path.join(self.project_root, 'instance', 'production.db')
            db_dir = os.path.dirname(db_path)
            
            if not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # 데이터베이스 초기화 스크립트 실행
            init_script = os.path.join(self.project_root, 'init_admin.py')
            if os.path.exists(init_script):
                subprocess.run([sys.executable, init_script], check=True, capture_output=True)
            
            logger.info("✅ 데이터베이스 설정 완료")
            
            return {
                "success": True,
                "database_path": db_path,
                "database_initialized": True
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _setup_security(self) -> Dict[str, Any]:
        """보안 설정"""
        try:
            security_configs = {
                "ssl_enabled": False,  # 개발 환경에서는 비활성화
                "csrf_protection": True,
                "session_secure": True,
                "password_hashing": True,
                "rate_limiting": True
            }
            
            # 보안 설정 파일 생성
            security_file = os.path.join(self.project_root, 'config', 'security.py')
            os.makedirs(os.path.dirname(security_file), exist_ok=True)
            
            with open(security_file, 'w', encoding='utf-8') as f:
                f.write(self._get_security_config())
            
            logger.info("✅ 보안 설정 완료")
            
            return {
                "success": True,
                "security_configs": security_configs,
                "security_file": security_file
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _get_security_config(self) -> str:
        """보안 설정 내용"""
        return '''"""
보안 설정
프로덕션 환경을 위한 보안 설정
"""

# SSL 설정
SSL_ENABLED = False
SSL_CERT_PATH = None
SSL_KEY_PATH = None

# CSRF 보호
CSRF_ENABLED = True
CSRF_TIME_LIMIT = 3600

# 세션 보안
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 3600

# 비밀번호 해싱
PASSWORD_HASH_METHOD = 'bcrypt'
PASSWORD_SALT_LENGTH = 16

# 속도 제한
RATE_LIMIT_ENABLED = True
RATE_LIMIT_DEFAULT = "200 per day;50 per hour"
RATE_LIMIT_STORAGE_URL = "memory://"

# 파일 업로드 보안
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# 로그 보안
LOG_SECURITY_EVENTS = True
LOG_FAILED_LOGINS = True
LOG_SENSITIVE_OPERATIONS = True
'''
    
    def setup_monitoring(self) -> Dict[str, Any]:
        """모니터링 설정"""
        logger.info("📊 모니터링 설정 시작")
        
        try:
            # 모니터링 스크립트 생성
            monitoring_script = os.path.join(self.project_root, 'scripts', 'monitoring.py')
            if not os.path.exists(monitoring_script):
                with open(monitoring_script, 'w', encoding='utf-8') as f:
                    f.write(self._get_monitoring_script())
            
            # 알림 설정
            notification_config = self._setup_notifications()
            
            # 백업 스케줄 설정
            backup_config = self._setup_backup_schedule()
            
            logger.info("✅ 모니터링 설정 완료")
            
            return {
                "success": True,
                "monitoring_script": monitoring_script,
                "notification_config": notification_config,
                "backup_config": backup_config
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _setup_notifications(self) -> Dict[str, Any]:
        """알림 설정"""
        return {
            "email_notifications": True,
            "slack_notifications": False,
            "alert_thresholds": {
                "cpu_usage": 80.0,
                "memory_usage": 85.0,
                "disk_usage": 90.0,
                "error_rate": 5.0
            }
        }
    
    def _setup_backup_schedule(self) -> Dict[str, Any]:
        """백업 스케줄 설정"""
        return {
            "daily_backup": True,
            "weekly_backup": True,
            "monthly_backup": True,
            "backup_retention_days": 30
        }
    
    def _get_monitoring_script(self) -> str:
        """모니터링 스크립트 내용"""
        return '''"""
시스템 모니터링 스크립트
시스템 상태를 모니터링하고 알림을 전송합니다.
"""

import psutil
import time
import logging
from datetime import datetime

def monitor_system():
    """시스템 모니터링"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # 임계값 확인
    alerts = []
    if cpu_percent > 80:
        alerts.append(f"CPU 사용률 높음: {cpu_percent}%")
    
    if memory.percent > 85:
        alerts.append(f"메모리 사용률 높음: {memory.percent}%")
    
    if disk.percent > 90:
        alerts.append(f"디스크 사용률 높음: {disk.percent}%")
    
    # 알림 전송
    if alerts:
        for alert in alerts:
            print(f"경고: {alert}")
    
    return {
        "cpu_percent": cpu_percent,
        "memory_percent": memory.percent,
        "disk_percent": disk.percent,
        "alerts": alerts
    }

if __name__ == "__main__":
    while True:
        monitor_system()
        time.sleep(60)  # 1분마다 체크
'''
    
    def setup_security(self) -> Dict[str, Any]:
        """보안 설정"""
        logger.info("🔒 보안 설정 시작")
        
        try:
            # 방화벽 설정 (시뮬레이션)
            firewall_config = self._setup_firewall()
            
            # SSL 인증서 설정 (시뮬레이션)
            ssl_config = self._setup_ssl_certificates()
            
            # 접근 권한 설정
            access_config = self._setup_access_control()
            
            # 데이터 암호화 설정
            encryption_config = self._setup_data_encryption()
            
            logger.info("✅ 보안 설정 완료")
            
            return {
                "success": True,
                "firewall": firewall_config,
                "ssl": ssl_config,
                "access_control": access_config,
                "encryption": encryption_config
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _setup_firewall(self) -> Dict[str, Any]:
        """방화벽 설정"""
        return {
            "enabled": True,
            "allowed_ports": [5000, 80, 443],
            "blocked_ips": []
        }
    
    def _setup_ssl_certificates(self) -> Dict[str, Any]:
        """SSL 인증서 설정"""
        return {
            "enabled": False,  # 개발 환경에서는 비활성화
            "cert_path": None,
            "key_path": None
        }
    
    def _setup_access_control(self) -> Dict[str, Any]:
        """접근 권한 설정"""
        return {
            "admin_required": True,
            "session_timeout": 3600,
            "max_login_attempts": 5
        }
    
    def _setup_data_encryption(self) -> Dict[str, Any]:
        """데이터 암호화 설정"""
        return {
            "database_encryption": False,
            "file_encryption": False,
            "transmission_encryption": True
        }
    
    def get_setup_summary(self) -> Dict[str, Any]:
        """설정 결과 요약"""
        if not self.setup_results:
            return {"error": "설정이 실행되지 않았습니다."}
        
        return {
            "overall_success": self.setup_results.get("overall_success", False),
            "system_requirements_passed": self.setup_results.get("system_requirements", {}).get("success", False),
            "dependencies_installed": self.setup_results.get("dependencies", {}).get("success", False),
            "environment_configured": self.setup_results.get("environment_variables", {}).get("success", False),
            "logging_configured": self.setup_results.get("logging_directories", {}).get("success", False),
            "cache_configured": self.setup_results.get("cache_directories", {}).get("success", False),
            "database_configured": self.setup_results.get("database", {}).get("success", False),
            "security_configured": self.setup_results.get("security", {}).get("success", False),
            "timestamp": self.setup_results.get("timestamp", "")
        }


def main():
    """메인 실행 함수"""
    try:
        setup = ProductionEnvironmentSetup()
        
        # 환경 설정
        results = setup.setup_environment()
        
        if results.get("overall_success", False):
            print("✅ 프로덕션 환경 설정이 성공적으로 완료되었습니다!")
            
            # 설정 요약 출력
            summary = setup.get_setup_summary()
            print(f"시스템 요구사항: {'✅' if summary['system_requirements_passed'] else '❌'}")
            print(f"의존성 설치: {'✅' if summary['dependencies_installed'] else '❌'}")
            print(f"환경 변수: {'✅' if summary['environment_configured'] else '❌'}")
            print(f"로깅 설정: {'✅' if summary['logging_configured'] else '❌'}")
            print(f"캐시 설정: {'✅' if summary['cache_configured'] else '❌'}")
            print(f"데이터베이스: {'✅' if summary['database_configured'] else '❌'}")
            print(f"보안 설정: {'✅' if summary['security_configured'] else '❌'}")
            
        else:
            print("❌ 프로덕션 환경 설정 중 오류가 발생했습니다.")
            if "error" in results:
                print(f"오류: {results['error']}")
                
    except Exception as e:
        print(f"❌ 예상치 못한 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 