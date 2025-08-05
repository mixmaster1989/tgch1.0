import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import time
from datetime import datetime

class MEXTradingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MEX Trading Bot Manager")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Переменные
        self.bot_process = None
        self.log_thread = None
        self.is_monitoring = False
        
        self.create_widgets()
        self.update_status()
    
    def create_widgets(self):
        # Главный фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="MEX Trading Bot Manager", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Кнопки управления
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_btn = ttk.Button(btn_frame, text="START", command=self.start_bot)
        self.start_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.restart_btn = ttk.Button(btn_frame, text="RESTART", command=self.restart_bot)
        self.restart_btn.grid(row=0, column=1, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="STOP", command=self.stop_bot)
        self.stop_btn.grid(row=0, column=2, padx=5)
        
        self.install_btn = ttk.Button(btn_frame, text="INSTALL", command=self.install_deps)
        self.install_btn.grid(row=0, column=3, padx=(5, 0))
        
        # Статус
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Checking...", 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Логи
        log_frame = ttk.LabelFrame(main_frame, text="Real-time Logs", padding="5")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Кнопки логов
        log_btn_frame = ttk.Frame(log_frame)
        log_btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.monitor_btn = ttk.Button(log_btn_frame, text="MONITOR LOGS", 
                                     command=self.toggle_log_monitoring)
        self.monitor_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.clear_btn = ttk.Button(log_btn_frame, text="CLEAR", 
                                   command=self.clear_logs)
        self.clear_btn.grid(row=0, column=1)
        
        # Настройка растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
    
    def run_command(self, command, show_output=True):
        """Выполнить команду в отдельном потоке"""
        def execute():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, 
                                      text=True, encoding='utf-8')
                if show_output:
                    self.log_message(f"Command: {command}")
                    if result.stdout:
                        self.log_message(result.stdout)
                    if result.stderr:
                        self.log_message(f"Error: {result.stderr}")
                return result.returncode == 0
            except Exception as e:
                self.log_message(f"Execution error: {str(e)}")
                return False
        
        thread = threading.Thread(target=execute)
        thread.daemon = True
        thread.start()
    
    def start_bot(self):
        """Запуск бота"""
        if self.is_bot_running():
            messagebox.showwarning("Warning", "Bot is already running!")
            return
        
        self.log_message("Starting MEX Trading Bot...")
        self.run_command("python main.py")
        self.root.after(2000, self.update_status)
    
    def restart_bot(self):
        """Перезапуск бота"""
        self.log_message("Restarting MEX Trading Bot...")
        self.run_command("taskkill /f /im python.exe", False)
        self.root.after(3000, lambda: self.run_command("python main.py"))
        self.root.after(5000, self.update_status)
    
    def stop_bot(self):
        """Остановка бота"""
        self.log_message("Stopping MEX Trading Bot...")
        self.run_command("taskkill /f /im python.exe")
        self.root.after(2000, self.update_status)
    
    def install_deps(self):
        """Установка зависимостей"""
        self.log_message("Installing dependencies...")
        self.run_command("pip install -r requirements.txt")
    
    def is_bot_running(self):
        """Проверить, запущен ли бот"""
        try:
            result = subprocess.run("tasklist /fi \"imagename eq python.exe\"", 
                                  shell=True, capture_output=True, text=True)
            return "python.exe" in result.stdout
        except:
            return False
    
    def update_status(self):
        """Обновить статус"""
        if self.is_bot_running():
            self.status_label.config(text="BOT RUNNING", foreground="green")
        else:
            self.status_label.config(text="BOT STOPPED", foreground="red")
        
        # Повторить через 5 секунд
        self.root.after(5000, self.update_status)
    
    def log_message(self, message):
        """Добавить сообщение в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def toggle_log_monitoring(self):
        """Включить/выключить мониторинг логов"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.monitor_btn.config(text="MONITOR LOGS")
            self.log_message("Log monitoring stopped")
        else:
            self.is_monitoring = True
            self.monitor_btn.config(text="STOP MONITORING")
            self.log_message("Log monitoring started")
            self.start_log_monitoring()
    
    def start_log_monitoring(self):
        """Запустить мониторинг логов"""
        def monitor():
            if not os.path.exists("bot.log"):
                return
            
            try:
                with open("bot.log", "r", encoding="utf-8") as f:
                    f.seek(0, 2)  # В конец файла
                    while self.is_monitoring:
                        line = f.readline()
                        if line:
                            self.root.after(0, lambda l=line: self.log_text.insert(tk.END, l))
                            self.root.after(0, lambda: self.log_text.see(tk.END))
                        else:
                            time.sleep(0.5)
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Monitoring error: {str(e)}"))
        
        if self.log_thread and self.log_thread.is_alive():
            return
        
        self.log_thread = threading.Thread(target=monitor)
        self.log_thread.daemon = True
        self.log_thread.start()
    
    def clear_logs(self):
        """Очистить логи"""
        self.log_text.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = MEXTradingBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()