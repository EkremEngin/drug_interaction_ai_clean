import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import pickle

# ===========================================
# 1) DOSYA YOLLARI
# ===========================================
DATA_PATH = r"C:/Users/Ekoreiz/drug_interaction_ai/data/balanced_ddi.csv"
VEC_PATH = r"C:/Users/Ekoreiz/drug_interaction_ai/models/vectorizer.pkl"
MODEL_PATH = r"C:/Users/Ekoreiz/drug_interaction_ai/models/interaction_model.pkl"

print("Balanced dataset yükleniyor...")
df = pd.read_csv(DATA_PATH)
print("Dataset şekli:", df.shape)

# ===========================================
# 2) TEXT + SEVERITY AL
# ===========================================
X = df["text"]
y = df["severity"].astype(int)

# ===========================================
# 3) TRAIN / TEST / VALID SPLIT
# ===========================================
print("Dataset train/val/test olarak bölünüyor...")

X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

X_val, X_test, y_val, y_test = train_test_split(
    X_temp, y_temp, test_size=0.50, random_state=42, stratify=y_temp
)

print(f"Train: {len(X_train)}")
print(f"Validation: {len(X_val)}")
print(f"Test: {len(X_test)}")

# ===========================================
# 4) TF-IDF VEKTORIZER (1–2 GRAM)
# ===========================================
print("TF-IDF vectorizer oluşturuluyor...")

vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=2,
    max_df=0.95
)

X_train_vec = vectorizer.fit_transform(X_train)
X_val_vec = vectorizer.transform(X_val)
X_test_vec = vectorizer.transform(X_test)

print("TF-IDF hazır. Toplam kelime sayısı:", len(vectorizer.vocabulary_))

# ===========================================
# 5) MODEL OLUŞTURMA
# ===========================================
print("Model eğitiliyor...")

model = LogisticRegression(
    max_iter=700,
    class_weight="balanced",
    n_jobs=-1,
    multi_class="auto"
)

model.fit(X_train_vec, y_train)

print("Model eğitimi tamamlandı.")

# ===========================================
# 6) VALIDATION & TEST PERFORMANSI
# ===========================================
print("\n=== VALIDATION SET SONUÇLARI ===")
y_val_pred = model.predict(X_val_vec)
print(classification_report(y_val, y_val_pred))

print("\n=== TEST SET SONUÇLARI ===")
y_test_pred = model.predict(X_test_vec)
print(classification_report(y_test, y_test_pred))

print("\n=== CONFUSION MATRIX (TEST SET) ===")
print(confusion_matrix(y_test, y_test_pred))

# ===========================================
# 7) MODELİ KAYDET
# ===========================================
with open(VEC_PATH, "wb") as f:
    pickle.dump(vectorizer, f)

with open(MODEL_PATH, "wb") as f:
    pickle.dump(model, f)

print("\n✔ Model kaydedildi:")
print("Vectorizer:", VEC_PATH)
print("Model:", MODEL_PATH)
