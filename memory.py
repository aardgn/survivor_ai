import chromadb
import uuid

class VectorMemory:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./ajan_hafizasi")
        self.collection = self.client.get_or_create_collection(name="anilar")
    def ani_ekle(self, ajan_id, metin):
        ani_id = str(uuid.uuid4())
        self.collection.add(
            documents=[metin],
            metadatas=[{"ajan": ajan_id}],
            ids=[ani_id]
        )
    def ani_hatirla(self, ajan_id, sorgu):
        sonuclar = self.collection.query(
            query_texts=[sorgu],
            n_results=1,
            where={"ajan": ajan_id}
        )
        if sonuclar["documents"] and sonuclar["documents"][0]:
            return sonuclar["documents"][0][0]
        return "Bu konu hakkında geçmişten bir şey hatırlamıyorum."