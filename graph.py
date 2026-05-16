from typing import TypedDict
from langgraph.graph import StateGraph, END
# brain.py içindeki hazır modellerimizi ve kuralcı parser'ımızı çekiyoruz
from brain import llm_gemini, llm_groq, parser 

# 1. GRAPH STATE: Düğümler arası taşınacak veriler
class AgentState(TypedDict):
    ajan_tip: str          # gemini mi llama mı?
    prompt_metni: str      # Dünya durumu (simülasyondan gelen)
    strateji: str          # 1. Düğümün ürettiği ham düşünce
    final_karar: dict      # 2. Düğümün ürettiği kesin JSON eylem

# 2. BİRİNCİ DÜĞÜM: Stratejist
def strateji_belirle(state: AgentState):
    prompt = f"{state['prompt_metni']}\n\nSadece mevcut durumu analiz et ve ne yapman gerektiğine dair 1-2 cümlelik bir strateji belirle. JSON KULLANMA, sadece ne yapacağını düşün."
    llm = llm_gemini if state['ajan_tip'] == "gemini" else llm_groq
    
    try:
        cevap = llm.invoke(prompt)
        # LangChain'den dönen objenin içindeki metni alıyoruz
        state["strateji"] = cevap.content if hasattr(cevap, 'content') else str(cevap)
    except Exception as e:
        state["strateji"] = "Zihnim bulanık, hayatta kalmaya odaklanmalıyım."
    
    return state

# 3. İKİNCİ DÜĞÜM: Eylemci
def eylem_sec(state: AgentState):
    format_talimati = parser.get_format_instructions()
    prompt = f"DÜNYA DURUMU: {state['prompt_metni']}\n\nSTRATEJİN: {state['strateji']}\n\nBu stratejiye kesinlikle uyarak LÜTFEN SADECE AŞAĞIDAKİ JSON FORMATINDA CEVAP VER:\n{format_talimati}"
    llm = llm_gemini if state['ajan_tip'] == "gemini" else llm_groq
    
    try:
        cevap = llm.invoke(prompt)
        karar = parser.invoke(cevap)
        state["final_karar"] = karar
    except Exception as e:
        # Rate limite takılan ajan "bekle"mez, panikle yemek arar ve enerjisini normal hızda harcar
        state["final_karar"] = {"dusunce": "API limitine takıldım! Zihnim bulandı, içgüdüsel olarak dolanıyorum...", "fiziksel_eylem": "kaynak_topla", "sosyal_eylem": ""}
        
    return state

# 4. GRAFİĞİ İNŞA ETME
workflow = StateGraph(AgentState)

workflow.add_node("stratejist", strateji_belirle)
workflow.add_node("eylemci", eylem_sec)

workflow.set_entry_point("stratejist")
workflow.add_edge("stratejist", "eylemci")
workflow.add_edge("eylemci", END)

# Sistemi derle ve dışa aktar
ajan_beyin_agaci = workflow.compile()