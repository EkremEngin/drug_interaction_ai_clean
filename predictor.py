import re
import pickle
from typing import List, Tuple
from rapidfuzz import process, fuzz
from brand_map import load_brand_map

# Yeni eklenen:
from explanation_engine import generate


MODEL_PATH = "models/interaction_model.pkl"
VEC_PATH = "models/vectorizer.pkl"
WHITELIST_PATH = "data/whitelist_drugs.txt"

DEBUG = True


def log(*msg):
    if DEBUG:
        print("[DEBUG]", *msg)


brand_map = load_brand_map()
log("[predictor] brand_map yüklendi.")

try:
    with open(WHITELIST_PATH, "r", encoding="utf-8") as f:
        WHITELIST = set(x.strip().lower() for x in f if x.strip())
    log("[predictor] whitelist yüklendi. adet:", len(WHITELIST))
except FileNotFoundError:
    WHITELIST = set()
    log("[predictor] whitelist bulunamadı, boş set kullanılacak.")

BRAND_MAP_LOWER = {k.lower(): v.lower() for k, v in brand_map.items()}

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
log("[predictor] interaction_model yüklendi.")

with open(VEC_PATH, "rb") as f:
    vectorizer = pickle.load(f)
log("[predictor] vectorizer.pkl yüklendi.")


def clean_text(t: str) -> str:
    t = t.lower()
    t = (
        t.replace("’", " ")
        .replace("‘", " ")
        .replace("“", " ")
        .replace("”", " ")
        .replace("\"", " ")
        .replace("'", " ")
    )
    t = re.sub(r"[^a-z0-9çğıöşü\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def fuzzy_match_drug(word: str, candidates: List[str], threshold: int = 86) -> str | None:
    if not candidates:
        return None
    match = process.extractOne(word, candidates, scorer=fuzz.ratio)
    if not match:
        return None
    name, score, _ = match
    log("[FUZZY]", repr(word), "->", repr(name), "score=", score)
    if score >= threshold:
        return name
    return None


def extract_drugs(text: str) -> List[str]:
    cleaned = clean_text(text)
    log("[cleaned]", cleaned)
    tokens = cleaned.split()

    found: List[str] = []

    # DIRECT
    for t in tokens:
        if t in WHITELIST:
            log("[DIRECT]", t)
            found.append(t)

    # BRAND → GENERIC
    for t in tokens:
        if t in BRAND_MAP_LOWER:
            generic = BRAND_MAP_LOWER[t]
            if generic in WHITELIST:
                log("[BRAND]", t, "->", generic)
                found.append(generic)

    # FUZZY
    wl_list = list(WHITELIST)
    for t in tokens:
        if len(t) < 4:
            continue
        match = fuzzy_match_drug(t, wl_list, threshold=86)
        if match:
            found.append(match)

    return sorted(list(set(found)))


# Override kuralları
STRONG_QT_DRUGS = {
    "amiodarone", "sotalol", "dofetilide", "quinidine", "disopyramide"
}

MEDIUM_QT_DRUGS = {
    "azithromycin", "clarithromycin", "ciprofloxacin",
    "escitalopram", "sertraline", "sumatriptan", "ondansetron"
}

CNS_STRONG = {
    "alprazolam", "diazepam", "clonazepam",
    "tramadol", "morphine", "fentanyl", "pregabalin"
}

SEDATION_MEDIUM = {"cetirizine", "loratadine", "diphenhydramine"}

HEPATIC_RISK = {
    tuple(sorted(("clarithromycin", "simvastatin"))),
    tuple(sorted(("azithromycin", "simvastatin"))),
    tuple(sorted(("fluconazole", "atorvastatin"))),
}

GI_MEDIUM = {
    tuple(sorted(("diclofenac", "prednisolone"))),
    tuple(sorted(("naproxen", "prednisolone"))),
}

GI_STRONG = {
    tuple(sorted(("warfarin", "aspirin"))),
    tuple(sorted(("warfarin", "ibuprofen"))),
    tuple(sorted(("warfarin", "ketorolac"))),
}


def clinical_override(d1: str, d2: str, raw: int) -> Tuple[int, str]:
    a = d1.lower()
    b = d2.lower()
    pair = tuple(sorted((a, b)))

    if a in STRONG_QT_DRUGS or b in STRONG_QT_DRUGS:
        return 3, "QT_PROLONGATION_HIGH"

    if a in MEDIUM_QT_DRUGS or b in MEDIUM_QT_DRUGS:
        return max(raw, 2), "QT_PROLONGATION_MEDIUM"

    if a in CNS_STRONG and b in CNS_STRONG:
        return 3, "CNS_RESPIRATORY_DEPRESSION"

    if (a in CNS_STRONG and b in SEDATION_MEDIUM) or (b in CNS_STRONG and a in SEDATION_MEDIUM):
        return max(raw, 2), "CNS_SEDATION_MEDIUM"

    if pair in HEPATIC_RISK:
        return 3, "HEPATIC_HIGH"

    if pair in GI_STRONG:
        return 3, "GI_BLEED_HIGH"

    if pair in GI_MEDIUM:
        return max(raw, 2), "GI_BLEED_MEDIUM"

    if raw == 1:
        return 1, "LOW_RISK"

    return raw, "UNKNOWN"


def predict_pair(d1: str, d2: str) -> Tuple[int, str]:
    text = f"{d1} {d2}"
    vec = vectorizer.transform([text])
    raw = int(model.predict(vec)[0])
    return clinical_override(d1, d2, raw)


# ------------------------------------------------------------
# 🔥 API / UI FONKSİYONU — FULL EXPLANATION
# ------------------------------------------------------------

def predict_interactions(text: str, style: int = 1):
    drugs = extract_drugs(text)
    results = []

    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            d1 = drugs[i]
            d2 = drugs[j]

            sev, cat = predict_pair(d1, d2)

            explanation = generate(
                drug_a=d1,
                drug_b=d2,
                severity=sev,
                source="model",
                style=style,
                category=cat
            )

            results.append({
                "drug_1": d1,
                "drug_2": d2,
                "severity": sev,
                "category": cat,
                "explanation": explanation
            })

    return {
        "drugs": drugs,
        "pairs": results
    }


# ------------------------------------------------------------
# 🔥 TERMINAL MODU — Artık açıklama da gösteriyor
# ------------------------------------------------------------

def analyze(text: str) -> None:
    drugs = extract_drugs(text)
    print("\nBulunan ilaçlar:", drugs)
    print()

    pairs = []

    for i in range(len(drugs)):
        for j in range(i + 1, len(drugs)):
            d1 = drugs[i]
            d2 = drugs[j]
            sev, cat = predict_pair(d1, d2)

            print(f"{d1} + {d2} → severity={sev} | cat={cat}")

            explanation = generate(
                drug_a=d1,
                drug_b=d2,
                severity=sev,
                source="model",
                style=3,  # Terminal için full doktor modu
                category=cat
            )

            print(explanation)
            print("-" * 60)

            pairs.append((d1, d2, sev, cat))

    high = sum(1 for _, _, sev, _ in pairs if sev == 3)
    mid = sum(1 for _, _, sev, _ in pairs if sev == 2)
    low = sum(1 for _, _, sev, _ in pairs if sev == 1)

    print(f"\nÖzet: {high} yüksek, {mid} orta, {low} hafif risk bulundu.")


if __name__ == "__main__":
    user_text = input("Ne kullandığını yaz: ")
    analyze(user_text)
