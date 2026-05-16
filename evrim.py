import json
import random
import time
import threading
import uuid
import re
import math
import os
from datetime import datetime
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from config import GEMINI_KEY, GROQ_KEY
from brain import get_llm_response
from agent import Ajan
from graph import ajan_beyin_agaci
app = Flask(__name__)
CORS(app)




def json_log_kaydet(tur, isim, dusunce, eylem, ham_cevap):
    dosya = "ajan_kararlar.json"
    kayit = {
        "zaman": str(datetime.now()),
        "tur": tur,
        "isim": isim,
        "dusunce": dusunce,
        "eylem": eylem,
        "orijinal_cevap": ham_cevap
    }
    try:
        if not os.path.exists(dosya):
            with open(dosya, "w", encoding="utf-8") as f:
                json.dump([kayit], f, ensure_ascii=False, indent=4)
        else:
            with open(dosya, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data.append(kayit)
                f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=4)
    except: pass


class Simulasyon:
    def __init__(self):
        from memory import VectorMemory
        self.uzun_hafiza = VectorMemory()

        self.tur = 0
        self.ajanlar = [Ajan() for _ in range(4)]
        self.kaynaklar = []
        self.bloklar = [
            {"id": "B1", "x": 300, "y": 300},
            {"id": "B2", "x": 500, "y": 300},
            {"id": "B3", "x": 400, "y": 200}
        ]
        self.olaylar = ["🌍 Nötr laboratuvar başarıyla başlatıldı."]
        self.lock = threading.Lock()
        self.aktif = True
        self.calisiyor = False 
        for _ in range(25): self.kaynak_ekle()

    def log(self, mesaj):
        self.olaylar.insert(0, f"[Tur {self.tur}] {mesaj}")
        if len(self.olaylar) > 50: self.olaylar.pop()

    def kaynak_ekle(self, miktar=1):
        for _ in range(miktar):
            self.kaynaklar.append({"id": str(uuid.uuid4())[:4], "x": random.randint(20, 780), "y": random.randint(20, 580), "deger": random.randint(30, 45)})

    def zeka_dongusu(self):
        indeks = 0
        while self.aktif:
            if self.calisiyor:
                with self.lock:
                    if not self.ajanlar: 
                        time.sleep(1); continue
                    
                    # İndeks, ajan sayısını geçerse turu bitir ve başa dön
                    if indeks >= len(self.ajanlar):
                        self.tur += 1
                        indeks = 0
                        if len(self.kaynaklar) < 20: self.kaynak_ekle(4)
                        
                    a = self.ajanlar[indeks]
                    digerleri = [aj.isim for aj in self.ajanlar if aj.isim != a.isim]
                    blok_str = ", ".join([b['id'] for b in self.bloklar])
                    mesaj_blogu = "\n".join(a.gelen_mesajlar[-3:]) if a.gelen_mesajlar else "Yok"

                    gorunen_kaynaklar = [k for k in self.kaynaklar if a.mesafe(k['x'], k['y']) < 250]
                    yemek_bilgisi = f"Etrafında {len(gorunen_kaynaklar)} adet yemek görüyorsun." if gorunen_kaynaklar else "Görüş alanında yemek YOK! Durursan açlıktan ölürsün. Haritayı keşfetmek için [kaynak_topla] eylemini seç ve hareket et!"
                    sorgu_metni = f"Rakiplerim {digerleri} varken geçmişte ne yapmıştım?"
                    hatirlanan_olay = self.uzun_hafiza.ani_hatirla(ajan_id=a.id, sorgu=sorgu_metni)

                with self.lock:
                    # Eğer enerji %30'un altındaysa ve yemek görüyorsa DÜŞÜNMEDEN yemeğe koş
                    if a.enerji < 60 and gorunen_kaynaklar:
                        a.dusunce = "İÇGÜDÜ: Açlıktan ölüyorum, API'yi bekleyecek vaktim yok, yemeğe koş!"
                        a.gecici_eylem = "kaynak_topla"
                        self.log(f"⚡ {a.isim} içgüdüsel olarak yemeğe atıldı.")
                        
                        indeks += 1
                        time.sleep(0.5) # Diğer ajana hızlı geç
                        continue
                prompt = f"""KİMLİK VE DURUM:
Adın: {a.isim} ({a.tip_adi})
Enerji: {a.enerji:.0f}/200
Kişilik: {a.kisilik}
Geçmişten Bir Anı: {hatirlanan_olay}
Rakipler: {digerleri}
Kutular: {blok_str}
Grup Üyelerin: {a.grup}
Hafıza: {' | '.join(a.hafiza)}
Mesajlar: {mesaj_blogu}

[YENİ DÜNYA KURALLARI VE ÖDÜLLER]:
1. GÖRÜŞ ALANI (SİS): {yemek_bilgisi}
2. SOSYAL SİNERJİ: Müttefiklerinle (grup üyelerinle) yan yana durursan %40 daha az yorulursun ve enerji tasarrufu sağlarsın!
3. KATI MADDELER: Kutular katıdır. Yolunu kapatıyorsa [it:KUTU_ID:yön] ile it.

Aynı anda hem hareket edip hem konuşabilirsin.
FİZİKSEL EYLEMLER (Sadece BİRİNİ seç): [kaynak_topla] veya [saldır:HEDEF_AD] veya [it:KUTU_ID:kuzey/guney/dogu/bati] veya [bekle]
SOSYAL EYLEMLER (İsteğe bağlı): [konus:HEDEF_AD:mesaj] veya [grup_teklif:HEDEF_AD] veya [grup_onay:HEDEF_AD]

DİKKAT: HEDEF_AD yazan yerlere kelimeyi kopyalamak yerine 'Rakipler' listesindeki gerçek bir ismi yaz!

ZORUNLU YANIT FORMATI:
[düşünce: karar alma mantığını açıkla]
[FİZİKSEL_KOMUT]
[SOSYAL_KOMUT] (Eğer istersen)"""
                
                # Eski karmaşık API çağırma kısmı yerine:
                # LangGraph Akışını Başlatıyoruz
                baslangic_durumu = {
                 "ajan_tip": a.brain['tip'],
                 "prompt_metni": prompt,
                 "strateji": "",
                 "final_karar": {}
             }

             # Ajan, hazırladığımız karar ağacından geçiyor
                sonuc_state = ajan_beyin_agaci.invoke(baslangic_durumu)

             # Çıkan kesin JSON kararını alıyoruz
                cevap = sonuc_state["final_karar"] 

                with self.lock:
                    a.son_karar = str(cevap) 
                    a.dusunce = cevap.get("dusunce", "Düşünemiyorum...")
                    
                    # Regex kullanmıyoruz, LangChain JSON sözlüğünü doğrudan okuyoruz
                    eylemler = [cevap.get("fiziksel_eylem", ""), cevap.get("sosyal_eylem", "")]
                    fiziksel_bulundu = False 
                    
                    for icerik in eylemler:
                        if not icerik: continue
                        p = icerik.split(':', 2)
                        tip = p[0].strip().lower().replace(" ", "_").replace("ı", "i")
                        
                        if tip == "konus":
                            hedef = p[1].strip() if len(p) > 1 else None; mesaj = p[2].strip() if len(p) > 2 else "..."
                            if hedef and hedef not in ["isim", "HEDEF_AD"] and hedef != a.isim:
                                h_aj = next((x for x in self.ajanlar if x.isim == hedef), None)
                                if h_aj: h_aj.gelen_mesajlar.append(f"{a.isim}: {mesaj}"); self.log(f"💬 {a.isim} -> {hedef}: {mesaj}")
                        elif tip == "grup_teklif":
                            hedef = p[1].strip() if len(p) > 1 else None
                            if hedef and hedef not in ["isim", "HEDEF_AD"] and hedef != a.isim:
                                h_aj = next((x for x in self.ajanlar if x.isim == hedef), None)
                                if h_aj: 
                                    if a.isim not in h_aj.teklifler: h_aj.teklifler.append(a.isim)
                                    h_aj.gelen_mesajlar.append(f"SİSTEM ÖNEMLİ: {a.isim} ittifak teklif etti. %40 enerji için Onay: [grup_onay:{a.isim}]")
                                    a.hafiza.append(f"{hedef}'e ittifak teklif ettim.")
                                    self.log(f"🤝 {a.isim}, {hedef}'e ittifak teklif etti.")
                        elif tip == "grup_onay":
                            hedef = p[1].strip() if len(p) > 1 else None
                            if hedef and hedef not in ["isim", "HEDEF_AD"] and hedef != a.isim:
                                if hedef in a.teklifler:
                                    h_aj = next((x for x in self.ajanlar if x.isim == hedef), None)
                                    if h_aj:
                                        if hedef not in a.grup: a.grup.append(hedef)
                                        if a.isim not in h_aj.grup: h_aj.grup.append(a.isim)
                                        if hedef in a.teklifler: a.teklifler.remove(hedef)
                                        self.log(f"🛡️ İTTİFAK: {a.isim} & {hedef} birleşti.")
                        elif tip == "it":
                            a.gecici_eylem = "it"; a.hedef_obje = p[1].strip() if len(p)>1 else None; a.hedef_yon = p[2].strip() if len(p)>2 else "kuzey"
                            fiziksel_bulundu = True
                        elif tip in ("kaynak_topla", "saldir", "saklan", "bekle"):
                            a.gecici_eylem = tip; a.hedef_isim = p[1].strip() if len(p)>1 else None
                            fiziksel_bulundu = True

                    if not fiziksel_bulundu: a.gecici_eylem = "kaynak_topla"
                    
                    if len(a.hafiza) > 6: a.hafiza.pop(0)
                    if len(a.gelen_mesajlar) > 4: a.gelen_mesajlar.pop(0)
                    
                    self.log(f"🧠 {a.isim} [{a.gecici_eylem}]: {a.dusunce}")
                    json_log_kaydet(self.tur, a.isim, a.dusunce, a.gecici_eylem, str(cevap))
                    anilacak_metin = f"{self.tur}. Tur biterken aklımdan şunlar geçti: {a.dusunce} ve sonucunda şu eylemi yaptım: {a.gecici_eylem}"
                    self.uzun_hafiza.ani_ekle(ajan_id=a.id, metin=anilacak_metin)


                indeks += 1
                time.sleep(4.5) 
            else: time.sleep(1)

    def fizik_dongusu(self):
        while self.aktif:
            if self.calisiyor:
                with self.lock:
                    olenler = []; yeni_nesil = []
                    for a in self.ajanlar:
                        tx, ty = None, None
                        
                        if a.gecici_eylem == "saldir" and a.hedef_isim:
                            h = next((x for x in self.ajanlar if x.isim == a.hedef_isim), None)
                            if h: 
                                tx, ty = h.x, h.y
                                if a.mesafe(tx, ty) < 25: 
                                    h.enerji -= 30; a.enerji += 15
                                    self.log(f"⚔️ {a.isim}, {h.isim}'e vurdu!")
                                    h.x += random.choice([-30, 30]); h.y += random.choice([-30, 30])
                                    a.gecici_eylem = "kaynak_topla" 
                        
                        elif a.gecici_eylem == "it" and a.hedef_obje:
                            b = next((x for x in self.bloklar if x["id"] == a.hedef_obje), None)
                            if b and a.mesafe(b['x'], b['y']) < 45:
                                d_it = 40
                                if a.hedef_yon == "kuzey": b['y'] -= d_it
                                elif a.hedef_yon == "guney": b['y'] += d_it
                                elif a.hedef_yon == "dogu": b['x'] += d_it
                                elif a.hedef_yon == "bati": b['x'] -= d_it
                                b["x"] = max(20, min(780, b["x"])); b["y"] = max(20, min(580, b["y"]))
                                self.log(f"📦 {a.isim}, {b['id']} kutusunu itti.")
                                a.gecici_eylem = "kaynak_topla"

                        if not tx and self.kaynaklar and a.gecici_eylem == "kaynak_topla":
                            gorunen_k = [k for k in self.kaynaklar if a.mesafe(k["x"], k["y"]) < 250]
                            if gorunen_k:
                                k = min(gorunen_k, key=lambda x: a.mesafe(x["x"], x["y"]))
                                tx, ty = k["x"], k["y"]
                            else:
                                if not hasattr(a, "kesif_x") or a.mesafe(a.kesif_x, a.kesif_y) < 20:
                                    a.kesif_x = random.uniform(50, 750) # Haritanın herhangi bir x noktası
                                    a.kesif_y = random.uniform(50, 550) # Haritanın herhangi bir y noktası
                                
                                tx, ty = a.kesif_x, a.kesif_y
                        
                        if tx and ty and a.gecici_eylem not in ("saklan", "bekle"):
                            d = a.mesafe(tx, ty)
                            if d > 5:
                                n_x = a.x + (tx - a.x) / d * a.hiz
                                n_y = a.y + (ty - a.y) / d * a.hiz
                                
                                carpti = False
                                carptigi_kutu = None
                                for b in self.bloklar:
                                    if abs(n_x - b['x']) < 35 and abs(n_y - b['y']) < 35:
                                        carpti = True; carptigi_kutu = b; break
                                
                                if not carpti:
                                    a.x, a.y = n_x, n_y
                                else:
                                    if a.x < carptigi_kutu['x']: a.x -= 2
                                    else: a.x += 2
                                    if a.y < carptigi_kutu['y']: a.y -= 2
                                    else: a.y += 2
                                    
                                    if "Önümde kutu var, yolum kapalı." not in a.hafiza:
                                        a.hafiza.append("Önümde kutu var, yolum kapalı.")

                        a.x = max(20, min(780, a.x))
                        a.y = max(20, min(580, a.y))

                        if a.gecici_eylem == "kaynak_topla":
                            for k in self.kaynaklar[:]:
                                if a.mesafe(k["x"], k["y"]) < 15:
                                    a.enerji += k["deger"]; self.kaynaklar.remove(k)

                        # Dinlenenler %50 tasarruf eder (0.02), ama sonsuza kadar yaşayamazlar.
                        enerji_harcamasi = 0.02 if a.gecici_eylem in ("saklan", "bekle") else 0.04
                        if a.grup:
                            for d_aj in self.ajanlar:
                                if d_aj.isim in a.grup and a.mesafe(d_aj.x, d_aj.y) < 150:
                                    enerji_harcamasi *= 0.6
                                    break
                        a.enerji -= enerji_harcamasi
                        
                        if a.enerji <= 0: olenler.append(a); self.log(f"💀 {a.isim} öldü.")
                        # --- EKLENEN KISIM: Üreme eşiği 180'e çekildi ve ebeveyn genleri aktarıldı ---
                        elif a.enerji >= 180:
                            a.enerji = 100; y = Ajan(nesil=a.nesil+1, anne_kisilik=a.kisilik, anne_hiz=a.hiz); y.x, y.y = a.x+20, a.y+20; yeni_nesil.append(y)
                            self.log(f"🌱 DOĞUM: {a.isim} üredi!")

                    self.ajanlar = [a for a in self.ajanlar if a not in olenler]
                    self.ajanlar.extend(yeni_nesil)
                    
                    if not self.ajanlar: 
                        self.ajanlar = [Ajan() for _ in range(4)]; self.kaynak_ekle(15)
            time.sleep(0.05)

print("DEBUG 1: Simülasyon nesnesi oluşturuluyor...")
sim = Simulasyon()

print("DEBUG 2: Simülasyon nesnesi başarıyla oluşturuldu, döngüler başlıyor...")
threading.Thread(target=sim.zeka_dongusu, daemon=True).start()
threading.Thread(target=sim.fizik_dongusu, daemon=True).start()

# ==========================================
# 🌐 WEB SUNUCUSU (FLASK ROUTES)
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/state')
def get_state():
    with sim.lock:
        ajan_verileri = []
        for a in sim.ajanlar:
            ajan_verileri.append({
                "id": a.id, "isim": a.isim, "emoji": a.tip_emoji, 
                "x": a.x, "y": a.y, "enerji": round(a.enerji, 1), 
                "eylem": a.gecici_eylem, "dusunce": a.dusunce, 
                "nesil": a.nesil, "kisilik": a.kisilik, 
                "grup_uyeleri": a.grup
            })
        return jsonify({
            "tur": sim.tur, "ajanlar": ajan_verileri, 
            "kaynaklar": sim.kaynaklar, "bloklar": sim.bloklar, 
            "olaylar": sim.olaylar, "calisiyor": sim.calisiyor
        })

@app.route('/toggle', methods=['POST'])
def toggle_sim():
    sim.calisiyor = not sim.calisiyor
    return jsonify({"status": "ok", "calisiyor": sim.calisiyor})
@app.route('/rizik', methods=['POST'])
def rizik_ver():
    with sim.lock:
        sim.kaynak_ekle(15)
        sim.log("☀ İLAHİ DOKUNUŞ: Gökten 15 adet rızık yağdı!")
    return jsonify({"status": "ok"})

@app.route('/felaket', methods=['POST'])
def felaket_ver():
    with sim.lock:
        sim.kaynaklar = [] # Tüm yemekleri sil
        for a in sim.ajanlar:
            a.enerji -= 30 # Herkese hasar vur
        sim.log("🌋 KURAKLIK! Tüm yemekler yandı, ajanlar 30 enerji kaybetti!")
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print("DEBUG 3: Flask sunucusu başlatılma komutu verildi!")
    app.run(debug=True, use_reloader=False)