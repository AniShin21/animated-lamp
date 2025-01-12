import os


class Config:

    API_ID = int(os.environ.get("API_ID", "15646796"))
    API_HASH = os.environ.get("API_HASH", "08bdb932cf2815a46b2a5f17cf245bfe")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "8083237896:AAGQBApSmHBn3kp4-cFL7Jyj2ILUvbS6qXY")
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002181491329"))
    DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://Lol:lolxd@cluster0.q5mtx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    AUTH_USERS = [int(i) for i in os.environ.get("AUTH_USERS", "6450266465").split(" ")]
    MAX_PROCESSES_PER_USER = int(os.environ.get("MAX_PROCESSES_PER_USER", 2))
    MAX_TRIM_DURATION = int(os.environ.get("MAX_TRIM_DURATION", 600))
    TRACK_CHANNEL = int(os.environ.get("TRACK_CHANNEL", False))
    SLOW_SPEED_DELAY = int(os.environ.get("SLOW_SPEED_DELAY", 5))
    HOST = os.environ.get("HOST", "gradual-larisa-animebotforpractice-f4065a4e.koyeb.app/")
    TIMEOUT = int(os.environ.get("TIMEOUT", 60 * 30))
    DEBUG = bool(os.environ.get("DEBUG"))
    WORKER_COUNT = int(os.environ.get("WORKER_COUNT", 20))
    IAM_HEADER = os.environ.get("IAM_HEADER", "")

    COLORS = [
        "white",
        "black",
        "red",
        "blue",
        "green",
        "yellow",
        "orange",
        "purple",
        "brown",
        "gold",
        "silver",
        "pink",
    ]
    FONT_SIZES_NAME = ["Small", "Medium", "Large"]
    FONT_SIZES = [30, 40, 50]
    POSITIONS = [
        "Top Left",
        "Top Center",
        "Top Right",
        "Center Left",
        "Centered",
        "Center Right",
        "Bottom Left",
        "Bottom Center",
        "Bottom Right",
    ]
