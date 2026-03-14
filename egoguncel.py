import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
import uvicorn
from typing import List, Dict, Any

app = FastAPI()

def get_ego_data(durak_no: str, hat_no: str = None):
    """EGO web sitesinden yeni 'bus-card' yapısına göre veri çeker."""
    url = "https://ego.gov.tr/otobusnerede"
    
    # Senin cURL verilerinden aldığımız kesin çalışan başlıklar
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://ego.gov.tr/otobusnerede"
    }
    
    # Önemli: SessionId zamanla değişebilir, eğer hata alırsan tarayıcıdan yenilemelisin
    cookies = {"ASP.NET_SessionId": "imqkqu21us1k5e3lskw515vp"}

    try:
        # EGO artık veriyi POST isteğiyle ve durak_no parametresiyle veriyor
        response = requests.post(url, data={"durak_no": durak_no}, headers=headers, cookies=cookies, timeout=10)
        
        if response.status_code != 200:
            return {"durum": "hata", "mesaj": f"EGO Sunucu Hatası: {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        bus_cards = soup.find_all('div', class_='bus-card')
        
        sonuclar = []

        for card in bus_cards:
            try:
                # Hat numarasını çek
                current_hat = card.find('div', class_='route-badge').text.strip()
                
                # Eğer kullanıcı spesifik bir hat sorduysa filtrele, sormadıysa hepsini getir
                if hat_no and current_hat != hat_no:
                    continue

                # Başlık ve Meta verileri (Plaka, Hız vb.)
                baslik = card.find('div', class_='route-title').text.strip()
                meta = card.find('div', class_='route-meta').text.strip().replace("\n", " ")
                
                # Tahmini Varış Süresi
                eta_div = card.find('div', class_='eta-mins')
                sure = eta_div.text.strip() if eta_div and eta_div.text.strip() else "Bekleniyor"

                sonuclar.append({
                    "hat": current_hat,
                    "guzergah": baslik,
                    "detay": meta,
                    "sure": sure,
                    "aktif": "dk" in sure # Eğer süre varsa araç yoldadır (aktif)
                })
            except AttributeError:
                continue

        if not sonuclar:
            return {"durum": "pasif", "mesaj": f"{durak_no} durağında aktif araç bulunamadı."}
            
        return {
            "durum": "aktif",
            "durak": durak_no,
            "araçlar": sonuclar
        }
            
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}

# --- API UÇ NOKTALARI ---

@app.get("/")
def home():
    return {
        "mesaj": "ArConnect EGO Canlı Takip API",
        "kullanim": "/sorgu/durak_no veya /sorgu/durak_no/hat_no"
    }

@app.get("/sorgu/{durak_no}")
def sorgula_tum(durak_no: str):
    """Duraktaki tüm hatları döner."""
    return get_ego_data(durak_no)

@app.get("/sorgu/{durak_no}/{hat_no}")
def sorgula_ozel(durak_no: str, hat_no: str):
    """Sadece istenen hattı döner."""
    return get_ego_data(durak_no, hat_no)

if __name__ == "__main__":
    # WearOS veya telefonun bağlanabilmesi için 0.0.0.0 önemli
    uvicorn.run(app, host="0.0.0.0", port=8000)
