# survivor_ai
A real-time multi-agent survival simulation powered by LangGraph, LLMs, and RAG (ChromaDB).
# Multi-Agent AI Survival Simulation

Bu proje, büyük dil modelleri (LLM) tarafından yönetilen otonom ajanların, sınırlı kaynaklara sahip bir haritada hayatta kalmaya çalıştığı, gerçek zamanlı bir evrim ve sosyal dinamik simülasyonudur.

Ajanlar sadece önceden yazılmış senaryoları oynamazlar; LangGraph tabanlı bir karar mekanizması, RAG destekli uzun süreli hafıza ve thread-safe bir fizik motoru kullanarak kendi özgür iradeleriyle hareket eder, savaşır, işbirliği yapar ve öğrenirler.

## Kullanılan Teknolojiler
* **Core:** Python 3.14, Flask (REST API & MVC Yapısı)
* **AI & Orkestrasyon:** LangChain, LangGraph, Llama-3.1 (Groq API) / Gemini API
* **Hafıza & Vektör DB:** ChromaDB, HuggingFace Sentence Transformers (all-MiniLM-L6-v2)
* **Mimari Kavramlar:** Multi-Agent Systems, RAG, Asynchronous Threading, Mutex Locks, Fallback Mechanisms

---

## 🧠 Karşılaşılan Mühendislik Zorlukları ve Çözümler

Simülasyonu canlı ortama alırken karşılaştığım temel mimari darboğazlar ve bunlara getirdiğim sistem tabanlı çözümler şunlardır:

### 1.Cognitive Bottleneck ve Hibrit Mimari
* **Sorun:** Fizik motorunun çalışma hızı ile LLM API'sinin yanıt süresi arasındaki asenkronluk, ajanların karar beklerken eylemsizlikten ölmesine yol açıyordu.
* **Çözüm:** Sisteme hibrit bir karar mekanizması entegre ettim. Ajanların enerji seviyeleri kritik eşiğin altına düştüğünde, pahalı ve yavaş olan LLM çağrısını tamamen bypass eden deterministik bir fallback sistemi devreye girer. Bu sayede sistem, otonomiyi kaybetmeden ağ gecikmelerini tolere edebilir hale geldi.

### 2. API Rate Limit ve Zarif Zayıflama (Graceful Degradation)
* **Sorun:** Çoklu ajanların aynı anda model API'lerine istek atması, limitlerin aşılmasına ve fırlatılan Exception'lar yüzünden simülasyonun donmasına neden oluyordu.
* **Çözüm:** Hata toleransı (**Fault Tolerance**) prensiplerini uygulayarak, API'nin koptuğu veya rate limit'e takıldığı anlarda programın çökmesini engelledim. Bu durumlarda ajanları "bekleme" moduna alarak deadlock yaratmak yerine, zeka seviyelerini geçici olarak düşürüp onları hayatta kalmaya (kaynak toplamaya) zorlayan bir graceful degradation mekanizması kurdum.

### 3. Bağlam Penceresi (Context Window) Sınırları ve RAG 
* **Sorun:** Bir ajanın doğumundan itibaren yaşadığı tüm olayları (logları) bir array içinde tutup her turda LLM'e göndermek, modelin token limitini anında dolduracak ve maliyet/gecikme yaratacaktı.
* **Çözüm:** ChromaDB kullanarak sisteme bir RAG mimarisi kurdum. Ajanlar, prompt'a tüm geçmişlerini yüklemek yerine semantic search yaparak sadece mevcut durumla (örn: karşısındaki spesifik rakip) en alakalı geçmiş anılarını vektör veritabanından çekip bağlam olarak kullanır.

### 4. Gerçek Zamanlı Simülasyonda Yarış Durumu (Race Condition)
* **Sorun:** Hesaplama ve render/hareket mekanizmalarını Thread'ler yardımıyla asenkron çalıştırırken, paylaşılan belleğe aynı anda erişilmesi sistemde çökmelere yol açma riski taşıyordu.
* **Çözüm:** Kritik veri okuma ve yazma işlemlerini self.lock blokları içine alarak sistemi Thread-Safe hale getirdim. Bir döngü ajan verisini güncellerken, diğer döngünün okuma yapmasını güvenli bir şekilde kilitledim.

---

## ⚙️ Kurulum ve Çalıştırma

Proje, özellikle yerel geliştirme ortamlarında Python 3.12+ sürümleriyle çalışacak şekilde optimize edilmiştir.

1. Repoyu klonlayın ve sanal ortam (venv) oluşturun:
```bash
git clone [https://github.com/aardgn/survivor_ai.git](https://github.com/aardgn/survivor_ai.git)
cd survivor_ai
python3 -m venv .venv
source .venv/bin/activate
