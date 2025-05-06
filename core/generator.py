import random
import yaml
import os
import time
from datetime import datetime
from gpt4all import GPT4All
import threading

# Путь к модели из конфигурации (будет загружен позже)
MODEL_PATH = None
MODEL_TEMPERATURE = 0.7
MODEL_MAX_TOKENS = 300

# Инициализация модели (ленивая загрузка)
_model = None
_model_lock = threading.Lock()

def load_config():
    """
    Загружает конфигурацию из файла
    
    Returns:
        dict: Конфигурация
    """
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"[ERROR] Ошибка при загрузке конфигурации: {e}")
        return {}

def init_model_config():
    """Инициализирует конфигурацию модели из файла config.yaml"""
    global MODEL_PATH, MODEL_TEMPERATURE, MODEL_MAX_TOKENS
    
    config = load_config()
    if 'model' in config:
        MODEL_PATH = config['model'].get('path', "/home/user1/.cache/gpt4all/Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf")
        MODEL_TEMPERATURE = config['model'].get('temperature', 0.7)
        MODEL_MAX_TOKENS = config['model'].get('max_tokens', 300)
        print(f"[INFO] Загружена конфигурация модели: {MODEL_PATH}")
    else:
        MODEL_PATH = "/home/user1/.cache/gpt4all/Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf"
        print(f"[INFO] Используется путь к модели по умолчанию: {MODEL_PATH}")

# Инициализация конфигурации модели
init_model_config()

def get_model():
    """
    Ленивая инициализация модели GPT4All с блокировкой для потокобезопасности
    
    Returns:
        GPT4All: Инициализированная модель или None в случае ошибки
    """
    global _model
    
    # Если модель уже загружена, возвращаем её
    if _model is not None:
        return _model
    
    # Блокировка для предотвращения одновременной загрузки модели из разных потоков
    with _model_lock:
        # Повторная проверка после получения блокировки
        if _model is not None:
            return _model
            
        try:
            print(f"[INFO] Загрузка модели GPT4All из {MODEL_PATH}...")
            start_time = time.time()
            
            # Инициализация модели с явным указанием использования CPU
            _model = GPT4All(
                model_path=MODEL_PATH,
                model_type="llama",  # Указываем тип модели
                allow_download=False,  # Запрещаем автоматическую загрузку
                n_threads=4  # Ограничиваем количество потоков для CPU
            )
            
            end_time = time.time()
            print(f"[INFO] Модель GPT4All успешно загружена за {end_time - start_time:.2f} секунд")
            return _model
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки модели GPT4All: {e}")
            print("[INFO] Используем резервный генератор на основе шаблонов")
            return None

# Загрузка шаблонов и данных
def load_templates():
    """Загружает шаблоны для генерации постов"""
    # В будущем можно загружать из файла, пока используем встроенные шаблоны
    templates = {
        "informational": [
            "🔍 {topic}: что нужно знать\n\n{content}\n\n#полезно #{hashtag}",
            "📊 Тренды {year}: {topic}\n\n{content}\n\n👉 Подписывайтесь, чтобы быть в курсе! #{hashtag}",
            "❓ Вопрос дня: {question}\n\n{content}\n\n💬 Поделитесь своим мнением в комментариях! #{hashtag}"
        ],
        "promotional": [
            "🚀 НОВИНКА: {topic}\n\n{content}\n\n👇 Узнайте больше по ссылке в профиле #{hashtag}",
            "⚡️ СРОЧНО: {topic} - только сегодня!\n\n{content}\n\n⏰ Предложение ограничено! #{hashtag}",
            "💎 Эксклюзив для подписчиков: {topic}\n\n{content}\n\n🔥 Не упустите возможность! #{hashtag}"
        ],
        "educational": [
            "📚 Обучающий пост: {topic}\n\n{content}\n\n✅ Сохраняйте, чтобы не потерять! #{hashtag}",
            "🧠 {topic}: пошаговое руководство\n\n{content}\n\n📌 Сохраните этот пост! #{hashtag}",
            "📝 {topic}: что нужно запомнить\n\n{content}\n\n👨‍🏫 Больше полезных материалов в нашем канале! #{hashtag}"
        ],
        "entertaining": [
            "😂 {topic}: забавная история\n\n{content}\n\n🔥 Подписывайтесь на канал для хорошего настроения! #{hashtag}",
            "🎬 {topic}: интересные факты\n\n{content}\n\n👀 А вы знали об этом? #{hashtag}",
            "🎯 {topic} челлендж!\n\n{content}\n\n🏆 Делитесь своими результатами в комментариях! #{hashtag}"
        ]
    }
    return templates

def load_topics():
    """Загружает темы для генерации постов"""
    topics = {
        "tech": [
            "Искусственный интеллект", "Блокчейн", "Криптовалюты", 
            "Мобильные приложения", "Кибербезопасность", "Стартапы",
            "Программирование", "Гаджеты", "Умный дом", "Виртуальная реальность"
        ],
        "business": [
            "Инвестиции", "Маркетинг", "Предпринимательство", 
            "Личные финансы", "Управление временем", "Продуктивность",
            "Лидерство", "Нетворкинг", "Фриланс", "Удаленная работа"
        ],
        "lifestyle": [
            "Здоровье", "Фитнес", "Питание", "Путешествия", 
            "Мода", "Красота", "Отношения", "Саморазвитие",
            "Психология", "Медитация"
        ],
        "entertainment": [
            "Кино", "Музыка", "Игры", "Книги", "Сериалы", 
            "Хобби", "Искусство", "Фотография", "Юмор", "Мемы"
        ]
    }
    return topics

def load_content_blocks():
    """Загружает блоки контента для генерации постов"""
    content_blocks = {
        "tech": [
            "Последние исследования показывают, что {topic} может изменить нашу жизнь в ближайшие 5 лет. Эксперты прогнозируют революцию в этой области.",
            "Топ-5 трендов в сфере {topic}:\n1. Интеграция с повседневной жизнью\n2. Улучшение пользовательского опыта\n3. Снижение стоимости технологий\n4. Рост доступности для массового потребителя\n5. Новые бизнес-модели",
            "{topic} становится все более популярным. По данным исследований, рынок вырастет на 300% к 2025 году. Самое время начать изучать эту технологию!"
        ],
        "business": [
            "3 ключевых принципа успеха в {topic}:\n1. Постоянное обучение и адаптация\n2. Построение сильной сети контактов\n3. Фокус на решении реальных проблем клиентов",
            "Как начать свой путь в {topic} без больших вложений? Начните с малого, тестируйте идеи и быстро адаптируйтесь к обратной связи от клиентов.",
            "Ошибки новичков в {topic}:\n- Отсутствие четкого плана\n- Игнорирование конкуренции\n- Неправильная оценка рынка\n- Страх неудачи\n\nИзбегайте их, и ваши шансы на успех значительно вырастут!"
        ],
        "lifestyle": [
            "5 простых шагов к улучшению {topic}:\n1. Начинайте с малого\n2. Создайте регулярную привычку\n3. Отслеживайте прогресс\n4. Найдите единомышленников\n5. Празднуйте маленькие победы",
            "Миф о {topic}, в который все верят: «Нужно много денег/времени/ресурсов». На самом деле, главное — последовательность и правильный подход!",
            "Как {topic} влияет на качество жизни? Исследования показывают, что регулярная практика может улучшить настроение на 60% и повысить общую удовлетворенность жизнью."
        ],
        "entertainment": [
            "Топ-3 тренда в мире {topic} в этом сезоне:\n1. [Первый тренд]\n2. [Второй тренд]\n3. [Третий тренд]\n\nКакой вам нравится больше всего?",
            "Закулисье индустрии {topic}: что остается за кадром и о чем не рассказывают широкой публике? Эксклюзивные факты в нашем материале!",
            "История {topic} насчитывает уже более [X] лет. За это время многое изменилось, но главное осталось неизменным — это по-прежнему вызывает восторг у миллионов людей по всему миру."
        ]
    }
    return content_blocks

def load_questions():
    """Загружает вопросы для генерации постов"""
    questions = [
        "Как {topic} изменит нашу жизнь в ближайшие 5 лет?",
        "Стоит ли инвестировать время и деньги в {topic}?",
        "Какие навыки нужны для успеха в сфере {topic}?",
        "Как начать свой путь в {topic} с нуля?",
        "Что будет с {topic} через 10 лет?",
        "{topic}: тренд или пустышка?",
        "Как {topic} влияет на нашу повседневную жизнь?",
        "Какие проблемы решает {topic} и почему это важно?",
        "Кто является лидером в области {topic} и почему?",
        "{topic}: за и против. Что перевешивает?"
    ]
    return questions

def load_hashtags():
    """Загружает хэштеги для генерации постов"""
    hashtags = {
        "tech": ["технологии", "инновации", "будущее", "прогресс", "хайтек"],
        "business": ["бизнес", "успех", "деньги", "карьера", "рост"],
        "lifestyle": ["жизнь", "саморазвитие", "здоровье", "счастье", "баланс"],
        "entertainment": ["развлечения", "досуг", "отдых", "веселье", "хобби"]
    }
    return hashtags

def generate_ai_content(topic, post_type, category):
    """
    Генерирует контент с использованием модели GPT4All
    
    Args:
        topic (str): Тема поста
        post_type (str): Тип поста
        category (str): Категория поста
        
    Returns:
        str: Сгенерированный контент или None в случае ошибки
    """
    try:
        model = get_model()
        if model is None:
            return None
            
        # Формируем промпт для модели
        prompt = f"""Напиши короткий пост для Telegram-канала на тему "{topic}".
Тип поста: {post_type} (информационный, рекламный, обучающий или развлекательный).
Категория: {category} (технологии, бизнес, лайфстайл или развлечения).
Пост должен быть информативным, интересным и привлекательным для читателя.
Длина поста: 3-5 предложений.
Не используй эмодзи и хэштеги, я добавлю их сам.
"""
        
        print(f"[INFO] Генерация контента для темы: {topic}")
        start_time = time.time()
        
        # Устанавливаем таймаут для генерации
        timeout = 30  # секунд
        
        # Генерируем ответ с ограничением по времени
        try:
            # Генерируем ответ с настройками из конфигурации
            response = model.generate(
                prompt, 
                max_tokens=MODEL_MAX_TOKENS, 
                temp=MODEL_TEMPERATURE,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                n_batch=8  # Уменьшаем размер батча для экономии памяти
            )
            
            end_time = time.time()
            print(f"[INFO] Контент сгенерирован за {end_time - start_time:.2f} секунд")
            
            # Очищаем ответ от лишних пробелов и переносов строк
            content = response.strip()
            
            return content
        except Exception as e:
            print(f"[ERROR] Ошибка при генерации контента: {e}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Ошибка при генерации контента с помощью GPT4All: {e}")
        return None

def generate_post(post_type=None, category=None):
    """
    Генерирует пост для Telegram-канала
    
    Args:
        post_type (str, optional): Тип поста (informational, promotional, educational, entertaining)
        category (str, optional): Категория поста (tech, business, lifestyle, entertainment)
    
    Returns:
        str: Сгенерированный пост
    """
    templates = load_templates()
    topics = load_topics()
    content_blocks = load_content_blocks()
    questions = load_questions()
    hashtags = load_hashtags()
    
    # Если тип поста не указан, выбираем случайный
    if not post_type:
        post_type = random.choice(list(templates.keys()))
    
    # Если категория не указана, выбираем случайную
    if not category:
        category = random.choice(list(topics.keys()))
    
    # Выбираем случайный шаблон из выбранного типа
    template = random.choice(templates[post_type])
    
    # Выбираем случайную тему из выбранной категории
    topic = random.choice(topics[category])
    
    # Пытаемся сгенерировать контент с помощью AI
    ai_content = generate_ai_content(topic, post_type, category)
    
    if ai_content:
        content = ai_content
    else:
        # Если не удалось сгенерировать контент с помощью AI, используем шаблоны
        content = random.choice(content_blocks[category]).format(topic=topic.lower())
    
    # Выбираем случайный вопрос
    question = random.choice(questions).format(topic=topic.lower())
    
    # Выбираем случайный хэштег
    hashtag = random.choice(hashtags[category])
    
    # Текущий год
    year = datetime.now().year
    
    # Формируем пост
    post = template.format(
        topic=topic,
        content=content,
        question=question,
        hashtag=hashtag,
        year=year
    )
    
    return post

def generate_post_with_config(config_path=None):
    """
    Генерирует пост с учетом конфигурации канала
    
    Args:
        config_path (str, optional): Путь к файлу конфигурации
    
    Returns:
        str: Сгенерированный пост
    """
    # Если путь к конфигурации не указан, используем путь по умолчанию
    if not config_path:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
            
        # В будущем здесь можно добавить логику для учета конфигурации канала
        # Например, тематика канала, стиль постов и т.д.
        
        return generate_post()
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации: {e}")
        return generate_post()

if __name__ == "__main__":
    # Тестирование генератора
    print(generate_post())
    print("\n---\n")
    print(generate_post("educational", "tech"))