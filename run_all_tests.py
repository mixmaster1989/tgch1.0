#!/usr/bin/env python
import pytest
import sys
import os
import subprocess
import logging
from datetime import datetime
import shutil

# Настройка логирования
def setup_logging():
    log_dir = "test_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"test_run_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return log_file

def install_dependencies():
    """Установка зависимостей из requirements.txt"""
    logging.info("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logging.info("Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install dependencies: {e}")
        sys.exit(1)

def run_tests():
    """Запуск тестов с отчетом о покрытии"""
    logging.info("Starting test execution...")
    
    # Создаем директорию для отчетов если её нет
    coverage_dir = "coverage_reports"
    if not os.path.exists(coverage_dir):
        os.makedirs(coverage_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    coverage_report = os.path.join(coverage_dir, f"coverage_{timestamp}")
    
    # Запускаем тесты с покрытием
    test_args = [
        "-v",
        "--cov=.",
        f"--cov-report=html:{coverage_report}",
        "--cov-report=term-missing",
        "tests"
    ]
    
    try:
        exit_code = pytest.main(test_args)
        if exit_code == 0:
            logging.info("All tests passed successfully!")
        else:
            logging.error(f"Tests failed with exit code: {exit_code}")
        return exit_code
    except Exception as e:
        logging.error(f"Error during test execution: {e}")
        return 1

def cleanup():
    """Очистка временных файлов"""
    logging.info("Cleaning up temporary files...")
    # Удаляем файлы .pyc и директории __pycache__
    for root, dirs, files in os.walk("."):
        for dir_name in dirs:
            if dir_name == "__pycache__":
                shutil.rmtree(os.path.join(root, dir_name))
        for file_name in files:
            if file_name.endswith(".pyc"):
                os.remove(os.path.join(root, file_name))

if __name__ == "__main__":
    log_file = setup_logging()
    logging.info("Starting test suite execution")
    
    try:
        install_dependencies()
        exit_code = run_tests()
        cleanup()
        logging.info(f"Test execution completed. Log file: {log_file}")
        sys.exit(exit_code)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)