import random
import hashlib
import sqlite3
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

DB_PATH = "cat_language.db"

def init_db():
    """
    Ініціалізуємо базу даних, якщо її ще немає.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translations (
            text TEXT PRIMARY KEY, 
            cat_hash TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

init_db()  # Викликаємо при старті сервера

def generate_cat_hash(text, max_sounds=70):
    """
    Генерує "котячий хеш" на основі вхідного тексту.
    """
    words = text.lower().split()
    num_sounds = min(len(words), max_sounds)  # Кількість котячих слів = кількість англійських, але не більше 70
    
    # Варіації котячих звуків
    meow_variants = ["meow", "meoow", "meooow", "meeow", "mmeeoww"]
    purr_variants = ["purr", "purrr", "purrrr"]
    
    # Генеруємо хеш
    hash_value = hashlib.md5(text.encode()).hexdigest()
    random.seed(int(hash_value, 16))  # Ініціалізуємо random для детермінованості
    
    cat_hash = []
    for i in range(num_sounds):
        if random.random() < 0.15:  # 15% шанс вставити purr
            cat_hash.append(random.choice(purr_variants))
        else:
            cat_hash.append(random.choice(meow_variants))
    
    return " ".join(cat_hash)

def save_to_db(text, cat_hash):
    """
    Зберігає текст та його котячий хеш у базі даних.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO translations (text, cat_hash) VALUES (?, ?) ON CONFLICT(text) DO NOTHING", (text, cat_hash))
        conn.commit()
        print(f"✅ Збережено в БД: {text} → {cat_hash}")
    except sqlite3.Error as e:
        print(f"🚨 Помилка запису в БД: {e}")
    conn.close()

def translate_from_cat(cat_hash):
    """
    Перекладає котячий хеш назад у текст, якщо він є у базі.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("SELECT text FROM translations WHERE cat_hash = ?", (cat_hash,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        print(f"🔁 Перекладено назад: {cat_hash} → {result[0]}")
        return result[0]
    else:
        print(f"❌ Не знайдено перекладу для: {cat_hash}")
        return "Sorry, I don't understand"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/translate", methods=["POST"])
def translate():
    data = request.json
    text = data.get("text", "").strip()
    cat_hash = data.get("cat_hash", "").strip()
    
    if text:
        cat_hash = generate_cat_hash(text, max_sounds=70)
        save_to_db(text, cat_hash)
        return jsonify({"original": text, "cat_hash": cat_hash})
    elif cat_hash:
        translation = translate_from_cat(cat_hash)
        return jsonify({"cat_hash": cat_hash, "translation": translation})
    else:
        return jsonify({"error": "Invalid input"}), 400

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
