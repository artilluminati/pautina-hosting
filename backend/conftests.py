import sys
import os

# Абсолютный путь до папки backend/src
SRC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))

# Вставляем его в начало sys.path, чтобы `import src.app` сработал
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)