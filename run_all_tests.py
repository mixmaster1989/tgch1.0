import subprocess
import sys

if __name__ == "__main__":
    # Устанавливаем pytest и pytest-qt, если не установлены
    subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-qt"], check=True)
    # Запуск всех тестов в папке tests, вывод в results.txt
    with open("results.txt", "w", encoding="utf-8") as f:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests", "--tb=short", "-v", "--maxfail=20"
        ], stdout=f, stderr=subprocess.STDOUT)
    print("Тесты завершены. Результаты сохранены в results.txt") 