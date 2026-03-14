import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
import uvicorn

app = FastAPI()

def get_ego_data_specific(durak_no: str, hat_no: str):
    """EGO sitesinden sadece istenen hat numarasını ayıklar."""
    url = "https://ego.gov.tr/otobusnerede"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "Referer": "https://ego.gov.tr/otobusnerede",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    
    cookies = {"ASP.NET_SessionId": "imqkqu21us1k5e3lskw515vp"}

    try:
        # Tüm durak verisini çekiyoruz
        response = requests.post(url, data={"durak_no": durak_no}, headers=headers, cookies=cookies, timeout=10)
        
        if response.status_code != 200:
            return {"durum": "hata", "mesaj": "EGO sunucusuna ulaşılamıyor."}

        soup = BeautifulSoup(response.text, 'html.parser')
        bus_cards = soup.find_all('div', class_='bus-card')
        
        # Kartlar içinde sadece istenen hat_no'yu ara
        for card in bus_cards:
            current_hat = card.find('div', class_='route-badge').get_text(strip=True)
            
            # Hat numarası eşleşiyorsa veriyi al ve hemen döndür
            if current_hat == hat_no:
                baslik = card.find('div', class_='route-title').get_text(strip=True)
                meta = card.find('div', class_='route-meta').get_text(strip=True).replace("\n", " ")
                
                eta_div = card.find('div', class_='eta-mins')
                sure = eta_div.get_text(strip=True) if eta_div else "Bekleniyor"

                return {
                    "durum": "aktif",
                    "hat": current_hat,
                    "guzergah": baslik,
                    "detay": meta,
                    "sure": sure,
                    "durak": durak_no
                }

        # Döngü biter ve hat bulunamazsa
        return {"durum": "pasif", "mesaj": f"{hat_no} hattı için şu an aktif veri yok."}
            
    except Exception as e:
        return {"durum": "hata", "mesaj": str(e)}


@app.get("/sorgu/{durak_no}/{hat_no}")
def sorgula(durak_no: str, hat_no: str):
    # Fonksiyon sadece ilgili hattı döndürür
    return get_ego_data_specific(durak_no, hat_no)

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=10000)
