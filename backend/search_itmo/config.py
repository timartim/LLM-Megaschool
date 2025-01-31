import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY", "")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")
SEARCH_URL = os.getenv("SEARCH_URL", "")
KINOPOISK_URL = os.getenv("KINOPOISK_URL", "")
CX = os.getenv("CX", "")
NUM_ANSWERS = 3
MODEL_AUTH_KEY = os.getenv("MODEL_AUTH_KEY", "")
KEYWORDS = """
итмо itmo университет university санкт-петербург st. petersburg
образование education наука science исследования research
рейтинги rankings QS ARWU THE U.S. News 
национальный исследовательский университет national research university 
магистратура master's бакалавриат bachelor's аспирантура phd
кафедры faculties институт institute лаборатории labs 
технологии technology искусственный интеллект AI машинное обучение ML
программирование coding computer science кибербезопасность cybersecurity
физика physics оптика optics нанотехнологии nanotechnology
робототехника robotics инженерия engineering математика mathematics
абитуриенты поступление admission студенты students выпускники alumni
история history достижения achievements премии awards конференции conferences
онлайн-курсы online courses международное сотрудничество international collaboration
"""

