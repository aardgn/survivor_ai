import random
import math
import uuid
MODEL_HAVUZU = [
    {"tip": "llama", "model": "llama-3.1-8b-instant", "emoji": "⚡"}
]

ISIMLER = ["Kael","Mira","Dusk","Vael","Oryn","Seren","Thane","Lyra","Zeyr","Nova"]
KISILIKLER = ["meraklı", "temkinli", "sosyal", "yalnız", "agresif", "fırsatçı"]



class Ajan:
    def __init__(self, nesil=1, anne_kisilik=None, anne_hiz=None):
        self.brain = random.choice(MODEL_HAVUZU)
        self.id = str(uuid.uuid4())[:6]
        self.isim = random.choice(ISIMLER)
        self.nesil = nesil
        self.enerji = 100.0
        self.x = random.uniform(100, 700)
        self.y = random.uniform(100, 500)
        
        if anne_hiz is not None:
            self.hiz = anne_hiz + random.uniform(-0.3, 0.3)
        else:
            self.hiz = random.uniform(3.5, 5.5)
        
        self.tip_adi = self.brain['tip'].capitalize()
        self.tip_emoji = self.brain['emoji']
        
        if anne_kisilik is not None:
            if random.random() < 0.70: 
                self.kisilik = anne_kisilik
            else:                      
                self.kisilik = random.choice(KISILIKLER)
        else:
            self.kisilik = random.choice(KISILIKLER)
        
        self.son_karar = "Gözlemliyor..."
        self.dusunce = "Sisteme giriş yaptım."
        self.hafiza = []
        self.gecici_eylem = "kaynak_topla" 
        self.hedef_isim = None
        self.hedef_obje = None
        self.hedef_yon = None
        self.gelen_mesajlar = []
        self.grup = [] 
        self.teklifler = []

    def mesafe(self, tx, ty): return math.hypot(self.x - tx, self.y - ty)