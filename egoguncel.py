import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
import uvicorn

app = FastAPI()

def get_ego_data(durak_no: str, hat_no: str):
    """EGO web sitesinden canlı veriyi çeken ana fonksiyon."""
    url = f"https://www.ego.gov.tr/tr/otobusnerede?durak_no={durak_no}&hat_no={hat_no}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.ego.gov.tr/tr/otobusnerede"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # HTML içindeki kırmızı renkli varış süresini ara
        tahmin_etiketi = soup.find('b', style=lambda v: v and 'B80000' in v)
        
        if tahmin_etiketi:
            sure_metni = tahmin_etiketi.get_text(strip=True).replace("Tahmini Varış Süresi:", "").strip()
            
            # Alt bilgileri (Plaka, Araç No) çekmek için üst etikete (i) bakıyoruz
            detaylar = tahmin_etiketi.parent.get_text(separator="|").split("|")
            plaka = next((s.replace("Plaka:", "").strip() for s in detaylar if "Plaka:" in s), "Bilinmiyor")
            arac_no = next((s.replace("Araç No:", "").strip() for s in detaylar if "Araç No:" in s), "Bilinmiyor")
            
            return {
                "durum": "aktif",
                "sure": sure_metni,
                "plaka": plaka,
                "arac_no": arac_no,
                "hat": hat_no,
                "durak": durak_no
            }
        else:
            return {"durum": "pasif", "mesaj": "Şu an bu hatta aktif araç bulunamadı."}
            
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

# --- API UÇ NOKTALARI (WearOS Buraya Bağlanacak) ---

@app.get("/")
def home():
    return {"mesaj": "EGO Canlı Takip API Çalışıyor", "kullanim": "/sorgu/durak_no/hat_no"}

@app.get("/sorgu/{durak_no}/{hat_no}")
def sorgula(durak_no: str, hat_no: str):
    return get_ego_data(durak_no, hat_no)

if __name__ == "__main__":
    # Bilgisayarının IP adresini otomatik almak yerine 0.0.0.0 yaparak 
    # ağdaki diğer cihazların (telefon/saat) erişmesini sağlıyoruz.
    uvicorn.run(app, host="0.0.0.0", port=8000)