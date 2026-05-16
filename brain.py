import time
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from config import GEMINI_KEY, GROQ_KEY

# PYDANTIC: Modellerin kesinlikle uyması gereken JSON sözleşmesi
class AgentKarari(BaseModel):
    dusunce: str = Field(description="Ajanın o anki durum değerlendirmesi ve stratejisi.")
    fiziksel_eylem: str = Field(description="Şunlardan BİRİ: kaynak_topla, bekle, saldir:HEDEF, it:KUTU:YON")
    sosyal_eylem: str = Field(description="Varsa BİRİ: konus:HEDEF:mesaj, grup_teklif:HEDEF, grup_onay:HEDEF. Yoksa boş bırak.")

parser = JsonOutputParser(pydantic_object=AgentKarari)

# İki modeli de LangChain standartlarında başlatıyoruz
llm_gemini = ChatGoogleGenerativeAI(model="gemini-1.5-flash", api_key=GEMINI_KEY, temperature=0.7) if GEMINI_KEY else None
# Not: Llama 3.1 8b kullanıyoruz, model adını groq'un güncel adına göre ayarladık
llm_groq = ChatGroq(model="llama-3.1-8b-instant", api_key=GROQ_KEY, temperature=0.7) if GROQ_KEY else None

def get_llm_response(ajan_tip, model_adi, prompt_metni):
    """Gemini veya Groq üzerinden standart JSON çıktısı alır."""
    try:
        format_talimati = parser.get_format_instructions()
        tam_prompt = f"{prompt_metni}\n\nLÜTFEN SADECE AŞAĞIDAKİ JSON FORMATINDA CEVAP VER:\n{format_talimati}"
        
        # Ajanın beyni neyse o modeli tetikliyoruz (.invoke)
        if ajan_tip == "gemini" and llm_gemini:
            cevap = llm_gemini.invoke(tam_prompt)
        elif ajan_tip == "llama" and llm_groq:
            cevap = llm_groq.invoke(tam_prompt)
        else:
            return {"dusunce": "Beynim (API) bağlı değil.", "fiziksel_eylem": "bekle", "sosyal_eylem": ""}
        
        # Gelen metni güvenli bir Python sözlüğüne (dictionary) çeviriyoruz
        karar_sozlugu = parser.invoke(cevap)
        return karar_sozlugu
        
    except Exception as e:
        print(f"LangChain Uyarısı ({ajan_tip}): {e}")
        time.sleep(2)
        return {"dusunce": "Sistem hatası aldım, dinleniyorum.", "fiziksel_eylem": "bekle", "sosyal_eylem": ""}