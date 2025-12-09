import random
import re

RISK_TEXT = {
    1: "düşük",
    2: "orta",
    3: "yüksek"
}

SEVERITY_EFFECT_COUNT = {
    1: 4,
    2: 7,
    3: 10
}

ABBREVIATIONS = {
    "QT": "QT aralığı (kalbin elektriksel repolarizasyon süresi)",
    "EKG": "EKG (elektrokardiyogram)",
    "INR": "INR (kanın pıhtılaşma ölçümü)",
    "CNS": "merkezi sinir sistemi"
}

CATEGORY_FAMILY = {
    "GI_BLEED": "GI",
    "GI_BLEED_HIGH": "GI",
    "GI_BLEED_MEDIUM": "GI",
    "GI_IRRITATION": "GI",
    "GI": "GI",

    "QT_PROLONG": "QT",
    "QT_PROLONGATION": "QT",
    "QT_PROLONGATION_HIGH": "QT",
    "QT_PROLONGATION_MEDIUM": "QT",
    "QT_PROLONG_HIGH": "QT",
    "QT_PROLONG_MEDIUM": "QT",

    "CNS": "CNS",
    "CNS_SEDATION_MEDIUM": "CNS",
    "CNS_RESPIRATORY_DEPRESSION": "CNS",
    "INCREASED_SEDATION": "CNS",

    "HEPATIC": "HEPATIC",

    "LOW_RISK": "LOW_RISK",
    "UNKNOWN": "LOW_RISK"
}

FAMILY_INFO = {
    "GI": {
        "name": "Gastrointestinal kanama / irritasyon",
        "mechanism_simple": (
            "Bu kombinasyon mide ve bağırsak sisteminde tahriş ve kanama riskini artırabilir. "
            "Özellikle kanı sulandıran veya mideyi irrite eden ilaçların bir arada kullanılması, "
            "küçük bir tahrişi bile önemli bir kanamaya çevirebilir."
        ),
        "mechanism_technical": (
            "İlaçlardan biri veya her ikisi trombosit fonksiyonunu ve pıhtılaşma yanıtını bozabilir, "
            "aynı zamanda mide ve duodenum mukozasında koruyucu bariyeri zayıflatabilir. "
            "Bu durum kapiller ve yüzeyel damarların kolay açılmasına, üst veya alt gastrointestinal "
            "kanama odaklarının ortaya çıkmasına ve klinikte melena, hematemez veya hematokezya olarak "
            "izlenebilen kanamalara yol açabilir."
        ),
        "side_effects": [
            "Mide veya üst karın bölgesinde yanma ve ağrı",
            "Süregelen mide bulantısı veya kusma",
            "Kahve telvesi görünümünde koyu renk kusma",
            "Siyah, katran kıvamında dışkı",
            "Parlak kırmızı rektal kanama veya dışkıda taze kan",
            "Karında şişlik, dolgunluk ve hassasiyet",
            "Belirgin iştahsızlık",
            "Şiddetli halsizlik ve yorgunluk",
            "Ani baş dönmesi veya göz kararması",
            "Ayakta durunca tansiyon düşmesi hissi",
            "Çarpıntı ile birlikte nefes nefese kalma",
            "Soğuk terleme ve ciltte solukluk",
            "Ani bayılma veya bayılacak gibi olma hissi"
        ],
        "management": {
            1: [
                "Uzun süren mide yanması, hafif siyah dışkı veya alışılmadık mide rahatsızlığında hekiminize bilgi verin.",
                "Alkol ve ek mideyi tahriş eden ilaçların (NSAİİ vb.) aynı gün içinde gereksiz kullanımından kaçının."
            ],
            2: [
                "Dışkının belirgin şekilde siyahlaşması, kahverengi-koyu kusma veya artan baş dönmesi durumunda acil tıbbi değerlendirme gerekir.",
                "Kronik kan sulandırıcı ilaç kullanıyorsanız en kısa sürede koagülasyon testleri (örneğin INR) ile değerlendirme önerilir."
            ],
            3: [
                "Bu kombinasyon mümkünse kullanılmamalıdır; alternatif tedaviler düşünülmelidir.",
                "Kanlı kusma, siyah dışkı, ani düşkünlük veya bayılma varsa derhal acil servise başvurulmalıdır.",
                "Hastanede damar yolu açılması, kan sayımı ve gerekli ise endoskopik değerlendirme ve destek tedavisi gerekebilir."
            ]
        }
    },
    "QT": {
        "name": "Kalp ritmi / QT uzaması",
        "mechanism_simple": (
            "Bu kombinasyon kalbin elektriksel ritmini etkileyerek ritim bozukluğu riskini artırabilir. "
            "Bazı ilaçlar kalbin toparlanma süresini (QT aralığını) uzatır; bir araya geldiklerinde bu etki güçlenebilir."
        ),
        "mechanism_technical": (
            "Her iki ilaç da kardiyak repolarizasyonu uzatarak QT aralığını artırabilir. "
            "Bu durum özellikle hassas bireylerde torsades de pointes gibi malign ventriküler "
            "aritmileri tetikleyebilir ve senkop, nöbet benzeri ataklar veya ani kardiyak ölüm riskini yükseltebilir."
        ),
        "side_effects": [
            "Kalpte ani başlayan çarpıntı hissi",
            "Düzensiz veya atlamalı kalp atımı",
            "Çok hızlı veya beklenenden yavaş nabız",
            "Göğüste baskı, sıkışma veya rahatsızlık hissi",
            "Ani baş dönmesi ve göz kararması",
            "Kısa süreli bayılma veya bayılacak gibi olma hissi",
            "Ani başlayan nefes darlığı",
            "Eforla beklenenden fazla nefes nefese kalma",
            "Sebebi açıklanamayan ani zayıflık ve çökme hissi",
            "Nöbet benzeri kasılma veya bilinç kaybı"
        ],
        "management": {
            1: [
                "Ara ara olan hafif çarpıntı veya hafif baş dönmesini hekiminize bildirin.",
                "Elektrolit dengesini bozabilecek yoğun kusma/ishal dönemlerinde bu kombinasyondan kaçınmaya çalışın."
            ],
            2: [
                "Yeni başlayan belirgin çarpıntı, göğüs rahatsızlığı veya bayılma hissinde EKG ile QT aralığı değerlendirilmelidir.",
                "Daha önce QT uzaması, doğuştan uzun QT sendromu veya ciddi kalp hastalığı varsa kardiyoloji görüşü önerilir."
            ],
            3: [
                "QT uzatma potansiyeli yüksek iki ilacın birlikte kullanımından mümkün olduğunca kaçınılmalıdır.",
                "Kullanım zorunlu ise seri EKG ile QTc takibi yapılmalı, elektrolitler (özellikle potasyum ve magnezyum) izlenmelidir.",
                "Çarpıntı ile birlikte senkop veya nöbet benzeri durum gelişirse acil kardiyak değerlendirme gerekir."
            ]
        }
    },
    "CNS": {
        "name": "Merkezi sinir sistemi depresyonu / sedasyon",
        "mechanism_simple": (
            "Bu kombinasyon beyin ve sinir sistemini fazla baskılayabilir. "
            "İki sedatif veya uyuşturucu etki yapan ilacın birlikte alınması, aşırı uyku hali ve "
            "nefesin yavaşlaması gibi riskleri artırır."
        ),
        "mechanism_technical": (
            "Her iki ilaç da GABAerjik iletim, opioid reseptör aktivasyonu veya diğer inhibitör "
            "nöral yollar üzerinden santral sinir sistemi üzerinde depresan etki gösterebilir. "
            "Bu durum bilinç düzeyinde azalma, psikomotor performansta bozulma ve ağır olgularda "
            "solunum merkezinin baskılanmasına yol açabilir."
        ),
        "side_effects": [
            "Belirgin uyku hali ve uyanmakta güçlük",
            "Sersemlik ve çevreye karşı ilgisizlik",
            "Denge kaybı, sendeleme veya düşme eğilimi",
            "Konuşma bozulması, kelimeleri toparlayamama",
            "Zihinsel bulanıklık ve konsantrasyon güçlüğü",
            "Hafıza sorunları veya olayları hatırlayamama",
            "Yavaş ve yüzeysel solunum",
            "Nefes alıp verme aralarında uzun duraklamalar",
            "Gürültülü horlama ile birlikte nefes durması hissi",
            "Dudaklarda veya parmak uçlarında morarma",
            "Tepki vermede belirgin gecikme",
            "Bilincin kapanması veya cevap vermeme"
        ],
        "management": {
            1: [
                "Belirgin uyku hali ve sersemlikte araç kullanmaktan ve yüksekten düşme riski olan işlerden kaçının.",
                "Alkol ve diğer sakinleştirici maddelerle birlikte kullanımından kaçının."
            ],
            2: [
                "Hastanın uyandırılmasının zorlaştığı, yürürken ciddi dengesizlik yaşadığı durumlarda acil tıbbi değerlendirme gerekir.",
                "Doz azaltımı, ilaçlardan birinin kesilmesi veya daha güvenli alternatiflere geçiş için hekimle görüşülmelidir."
            ],
            3: [
                "Solunumun yavaşlaması, dudaklarda morarma veya hiç uyanmama durumunda acil müdahale gerekir.",
                "Bu düzeyde risk taşıyan kombinasyonlar mümkünse kullanılmamalı, gerekiyorsa yakın klinik izlem altında verilmelidir."
            ]
        }
    },
    "HEPATIC": {
        "name": "Karaciğer toksisitesi",
        "mechanism_simple": (
            "Bu kombinasyon karaciğer üzerinde ek yük oluşturabilir. "
            "Karaciğerde ilaç birikimi veya toksik metabolit oluşumu artarak karaciğer hasarı riskini yükseltebilir."
        ),
        "mechanism_technical": (
            "Karaciğer üzerinden metabolize olan ilaçların birlikte kullanımı, "
            "sitokrom P450 enzimlerinin inhibisyonu veya indüksiyonu yoluyla ilaç düzeylerinde artışa "
            "ve hepatoselüler hasara yol açabilir. Bu durum transaminaz yüksekliği, kolestaz veya "
            "karışık tip ilaç ilişkili karaciğer hasarı ile sonuçlanabilir."
        ),
        "side_effects": [
            "Göz aklarında sararma",
            "Ciltte sararma",
            "Sağ üst karında ağrı veya hassasiyet",
            "Karında dolgunluk ve şişkinlik hissi",
            "Belirgin iştah kaybı",
            "Süregelen bulantı veya kusma",
            "Koyu renk (çay renginde) idrar",
            "Açık renkli veya kil renginde dışkı",
            "Genel halsizlik ve çabuk yorulma",
            "Sebebi açıklanamayan kilo kaybı",
            "Tüm vücutta kaşıntı hissi",
            "Hafif ateş veya grip benzeri yakınmalar"
        ],
        "management": {
            1: [
                "Sarılık, koyu idrar veya açıklanamayan halsizlik fark ederseniz kısa sürede doktorunuza başvurun.",
                "Karaciğer hastalığı öykünüz varsa kontrolsüz ağrı kesici ve bitkisel ürün kullanımından kaçının."
            ],
            2: [
                "Uzayan bulantı, sağ üst karın ağrısı veya sarılık bulgularında karaciğer fonksiyon testleri yapılmalıdır.",
                "Karaciğer enzimleri yükselmişse doz azaltımı veya ilgili ilaçların kesilmesi gündeme gelebilir."
            ],
            3: [
                "Belirgin sarılık, koyu idrar, ileri halsizlik ve pıhtılaşma bozukluğu bulgularında acil hastane yatışı gerekebilir.",
                "İlaçların derhal kesilmesi ve hepatotoksik olası diğer ajanların gözden geçirilmesi önerilir."
            ]
        }
    },
    "LOW_RISK": {
        "name": "Düşük etkileşim riski",
        "mechanism_simple": (
            "Bu kombinasyon için model düşük düzeyde bir etkileşim riski öngörmektedir. "
            "Ciddi bir yan etki beklenmez; ancak her ilaç gibi bireysel farklılıklara bağlı hafif şikâyetler görülebilir."
        ),
        "mechanism_technical": (
            "Mevcut veriler bu kombinasyon için klinik açıdan belirgin bir farmakokinetik veya farmakodinamik "
            "etkileşim göstermemektedir. Yine de duyarlı bireylerde hafif yan etkiler veya nadir idiosenkratik "
            "reaksiyonlar ortaya çıkabilir."
        ),
        "side_effects": [
            "Hafif baş ağrısı",
            "Hafif mide bulantısı veya hazımsızlık",
            "Geçici baş dönmesi",
            "Hafif uyku hali veya sersemlik",
            "Ağız kuruluğu",
            "Hafif çarpıntı hissi"
        ],
        "management": {
            1: [
                "Hafif şikâyetler genelde kendiliğinden düzelebilir; yine de birkaç gün içinde geçmezse hekiminize danışın.",
                "Beklenmeyen veya hızla artan bir belirti olursa ilacı kesmeden önce mutlaka sağlık profesyoneli ile görüşün."
            ],
            2: [
                "Şikâyetler günlük yaşamı belirgin etkiliyorsa doz ayarlaması veya alternatif ilaçlar için hekim değerlendirmesi önerilir."
            ],
            3: [
                "Model düşük risk tahmin etse bile klinik olarak ciddi bulgu varsa acil tıbbi yardım önceliklidir."
            ]
        }
    }
}

DISCLAIMER = (
    "Bu açıklama bilgilendirme amaçlıdır; tanı veya tedavi kararı yerine geçmez. "
    "Her zaman kendi doktorunuzun önerilerini esas alın ve ciddi bir belirti durumunda acil yardım isteyin."
)


def expand_abbreviations(text):
    for short, long in ABBREVIATIONS.items():
        pattern = r"\b" + re.escape(short) + r"\b"
        text = re.sub(pattern, long, text)
    return text


def pick_effects(family, severity):
    info = FAMILY_INFO.get(family)
    if not info:
        return []
    effects = info.get("side_effects", [])
    if not effects:
        return []
    n = SEVERITY_EFFECT_COUNT.get(severity, 4)
    if n > len(effects):
        n = len(effects)
    if n <= 0:
        return []
    return random.sample(effects, n)


def ul(items):
    return "".join(f"<li>{item}</li>" for item in items)


def normalize_mode(mode):
    if isinstance(mode, int):
        return {1: "simple", 2: "intermediate", 3: "doctor"}.get(mode, "simple")
    if isinstance(mode, str):
        m = mode.lower()
        if m in ("simple", "basit"):
            return "simple"
        if m in ("intermediate", "orta", "medium"):
            return "intermediate"
        if m in ("doctor", "doktor", "advanced"):
            return "doctor"
    return "simple"


def build_explanation(drug_a, drug_b, category, severity, mode="simple"):
    if not isinstance(severity, int):
        try:
            severity = int(severity)
        except Exception:
            severity = 2
    if severity < 1:
        severity = 1
    if severity > 3:
        severity = 3

    family = CATEGORY_FAMILY.get(category, "LOW_RISK")
    info = FAMILY_INFO.get(family, FAMILY_INFO["LOW_RISK"])
    mode_norm = normalize_mode(mode)

    risk_text = RISK_TEXT.get(severity, "belirsiz")
    effects = pick_effects(family, severity)
    effects_html = ul(effects)

    mech_simple = expand_abbreviations(info.get("mechanism_simple", ""))
    mech_technical = expand_abbreviations(info.get("mechanism_technical", ""))

    management_list = info.get("management", {}).get(severity)
    if not management_list:
        management_list = info.get("management", {}).get(2, [])
    management_html = ul(management_list)

    pair = f"{drug_a} + {drug_b}"
    family_name = info.get("name", "")

    if mode_norm == "simple":
        return (
            f"<strong>{pair}</strong><br>"
            f"<strong>Risk seviyesi:</strong> {risk_text}<br>"
            f"<strong>Etkileşim tipi:</strong> {family_name}<br><br>"
            f"{mech_simple}<br><br>"
            f"<strong>Olası belirtiler:</strong>"
            f"<ul>{effects_html}</ul>"
            f"<p>{DISCLAIMER}</p>"
        )

    if mode_norm == "intermediate":
        return (
            f"<strong>{pair}</strong><br>"
            f"<strong>Risk seviyesi:</strong> {risk_text}<br>"
            f"<strong>Olası etkileşim tipi:</strong> {family_name}<br><br>"
            f"{mech_simple}<br><br>"
            f"<strong>Klinikte izlenebilecek bulgular:</strong>"
            f"<ul>{effects_html}</ul>"
            f"<strong>Klinik yaklaşım önerileri:</strong>"
            f"<ul>{management_html}</ul>"
            f"<p>{DISCLAIMER}</p>"
        )

    return (
        f"<strong>KOMBİNASYON:</strong> {pair}<br>"
        f"<strong>RİSK SEVİYESİ:</strong> {risk_text} (kategori: {family_name})<br><br>"
        f"<strong>MUHTEMEL MEKANİZMA:</strong><br>"
        f"{mech_technical}<br><br>"
        f"<strong>KLİNİK BULGULAR / SEMPTOM HAVUZU:</strong>"
        f"<ul>{effects_html}</ul>"
        f"<strong>YÖNETİM VE İZLEM:</strong>"
        f"<ul>{management_html}</ul>"
        f"<p>{DISCLAIMER}</p>"
    )


def generate(drug_a, drug_b, severity, source, style, category):
    mode = normalize_mode(style)
    return build_explanation(drug_a, drug_b, category, severity, mode)
