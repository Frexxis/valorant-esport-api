# Valorant Esports API

Bu API, Valorant esporları hakkında kapsamlı veriler sağlar. [vlr.gg](https://www.vlr.gg/) ve [bo3.gg](https://bo3.gg/) gibi kaynaklardan web kazıma yöntemiyle veri toplayarak, bunları düzenli olarak güncelleyen bir sistem oluşturulmuştur.

## Özellikler

- **Takımlar ve Oyuncular**: Takım bilgileri, oyuncu kadroları ve istatistikler
- **Maçlar**: Canlı, yaklaşan ve geçmiş maçlar hakkında bilgiler
- **Turnuvalar**: Devam eden ve yaklaşan turnuvalar hakkında bilgiler
- **Sürekli Güncelleme**: Her 5 dakikada bir canlı maçlar, her 30 dakikada bir tüm maçlar ve her 4 saatte bir takımlar güncellenir

## API Endpointleri

API, aşağıdaki endpointleri içerir:

### Takımlar

- `GET /api/teams`: Tüm takımları listeler
- `GET /api/teams/{team_id}`: Belirli bir takımın detaylarını verir
  - `?include_players=true`: Oyuncu kadrosunu dahil eder
  - `?refresh=true`: Veriyi kaynaktan yeniler

### Oyuncular

- `GET /api/players`: Tüm oyuncuları listeler
- `GET /api/players/{player_id}`: Belirli bir oyuncunun detaylarını verir

### Maçlar

- `GET /api/matches`: Tüm maçları listeler
- `GET /api/matches/{match_id}`: Belirli bir maçın detaylarını verir
- `GET /api/matches/live`: Şu anda canlı olan maçları verir
- `GET /api/matches/upcoming`: Yaklaşan maçları verir
- `GET /api/matches/recent`: En son tamamlanan maçları verir

### Arama

- `GET /api/search/teams?q={query}`: Takım adına göre arama yapar

## Kurulum ve Çalıştırma

### Gereksinimler

- Python 3.8+
- PostgreSQL veritabanı
- Gerekli Python paketleri (`requirements.txt` dosyasında belirtilmiştir)

### Adımlar

1. Repoyu klonlayın:
   ```
   git clone https://github.com/yourusername/valorant-esports-api.git
   cd valorant-esports-api
   ```

2. Sanal ortam oluşturun ve paketleri yükleyin:
   ```
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. PostgreSQL veritabanı bağlantı bilgilerini içeren bir `.env` dosyası oluşturun:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/valorant_api
   ```

4. Veritabanı tablolarını oluşturun:
   ```
   python -c "from app import app; from models import db; app.app_context().push(); db.create_all()"
   ```

5. Uygulamayı çalıştırın:
   ```
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

## Sürekli Çalışma

API'nin sürekli güncellenmesi için aşağıdaki seçeneklerden birini kullanabilirsiniz:

1. **Replit "Always On"**: Replit'te projenizi 7/24 çalışacak şekilde ayarlayabilirsiniz.

2. **Diğer Hosting Çözümleri**: Heroku, DigitalOcean, AWS gibi platformlarda da barındırabilirsiniz.

## Katkıda Bulunma

Katkılarınızı memnuniyetle karşılıyoruz! Lütfen bir pull request göndermeden önce şunlara dikkat edin:

1. Mevcut kod stiline uyun
2. Tüm testlerin başarıyla geçtiğinden emin olun
3. Yeni özellikleri dokümante edin

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır - daha fazla bilgi için LICENSE dosyasına bakın.

## Yasal Uyarı

Bu API, Riot Games ile ilişkili değildir ve Riot Games tarafından desteklenmemektedir.