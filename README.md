# Plaka Tanıma Sistemi (ANPR/LPR) — Windows Masaüstü Uygulaması

RTSP IP kameralardan görüntü alan, Türk araç plakalarını tespit edip okuyan,
kayıtlarını SQLite veritabanında tutan, PySide6 tabanlı koyu temalı bir
masaüstü uygulaması.

## İçindekiler

- [Özellikler](#özellikler)
- [Kullanılan Teknolojiler ve Lisanslar](#kullanılan-teknolojiler-ve-lisanslar)
- [Kurulum (Geliştirme — Windows)](#kurulum-geliştirme--windows)
- [Kamera Yapılandırma](#kamera-yapılandırma)
- [Demo/Test Modu](#demotest-modu)
- [Varsayılan Giriş Bilgileri](#varsayılan-giriş-bilgileri)
- [Testler](#testler)
- [EXE / Kurulum Paketi Üretimi](#exe--kurulum-paketi-üretimi)
- [Sorun Giderme](#sorun-giderme)
- [Bilinen Kısıtlar](#bilinen-kısıtlar)
- [Mimari](#mimari)

## Özellikler

- Çoklu RTSP IP kamera desteği (ekleme/düzenleme/silme/bağlantı testi), TCP taşıma tercihi
- Her kamera ayrı thread'de okunur; UI asla donmaz
- Bağlantı koptuğunda üstel geri çekilmeli otomatik yeniden bağlanma
- Gerçek plaka tespiti (OpenCV Haar cascade) + gerçek OCR (Tesseract)
- Türk plaka biçimi doğrulama ve OCR hata düzeltme (normalizasyon)
- Tespit/OCR güven skorları ayrı ayrı tutulur; düşük güven → "incelemeye işaretle"
- Aynı plakanın aynı kamerada kısa sürede tekrar kaydını önleyen dedup mekanizması
- SQLite veritabanı: cameras, detections, authorized_vehicles, users, application_settings, audit_logs
- Filtrelenebilir tespit kayıtları + CSV dışa aktarma
- Yetkili araç yönetimi ve otomatik eşleştirme
- Kayıt saklama süresi (retention) ayarı ve otomatik temizlik
- Kamera parolaları işletim sistemi kimlik bilgisi deposunda (Windows Credential Manager) saklanır, düz metin loglanmaz
- Kullanıcı girişi (PBKDF2-HMAC-SHA256 ile parola hashleme) ve denetim (audit) kaydı

## Kullanılan Teknolojiler ve Lisanslar

| Bileşen | Kütüphane | Lisans | Not |
|---|---|---|---|
| Arayüz | PySide6 (Qt for Python) | LGPL-3.0 | Dinamik bağlama ile kullanılır |
| Kamera/Görüntü | OpenCV (`opencv-python-headless`) | Apache 2.0 | |
| **Plaka tespiti** | OpenCV `haarcascade_russian_plate_number.xml` | Intel/BSD benzeri (OpenCV ile birlikte dağıtılır) | Gerçek, indirme gerektirmeyen, OpenCV kurulumuyla **gerçekten gelen** bir model. Türkiye'ye özel eğitilmemiştir; genel dikdörtgen plaka şekli tespit eder |
| **OCR** | Tesseract OCR (`pytesseract` sarmalayıcısı) | Apache 2.0 | Sistemde ayrıca kurulması gerekir (bkz. Kurulum) |
| Veritabanı | SQLite (Python stdlib `sqlite3`) | Public Domain | |
| Parola deposu | `keyring` | MIT | Windows'ta Credential Manager arka ucu |
| Paketleme | PyInstaller | GPL-2.0+ (çıktı EXE'niz bu lisansa tabi değildir) | |

**Neden YOLO + derin öğrenme tabanlı bir model değil?** Proje başında
kullanıcıyla netleştirildi: hazır, lisansı belirsiz olmayan, indirme
gerektirmeyen bir model/OCR çifti tercih edildi. Bu, daha düşük tespit
doğruluğu (özellikle açılı/düşük ışıklı görüntülerde) pahasına, %100
gerçek ve lisans riski taşımayan bir temel sağlar. İleride bir
YOLOv8/Türkçe plaka modeli ile `app/recognition/detector.py` değiştirilerek
doğruluk artırılabilir (bkz. Bilinen Kısıtlar).

## Kurulum (Geliştirme — Windows)

1. **Python 3.11** kurun (https://www.python.org/downloads/, "Add to PATH" işaretleyin).
2. **Tesseract OCR** kurun: https://github.com/UB-Mannheim/tesseract/wiki
   - Kurulum sırasında "Additional language data" içinden **Turkish** paketini de seçin.
   - Kurulum dizinini (`C:\Program Files\Tesseract-OCR`) sistem PATH'ine ekleyin.
3. Proje klasöründe:
   ```
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Uygulamayı başlatın:
   ```
   run.bat
   ```
   veya
   ```
   python main.py
   ```

İlk açılışta veritabanı otomatik oluşturulur (`%LOCALAPPDATA%\PlakaTanimaSistemi\data\plaka_tanima.db`)
ve varsayılan bir yönetici kullanıcı eklenir (bkz. [Varsayılan Giriş Bilgileri](#varsayılan-giriş-bilgileri)).

## Kamera Yapılandırma

"Kamera Yönetimi" ekranından **+ Kamera Ekle** ile:

1. Kamera adı, host/IP, port (varsayılan 554), ana akış yolu (örn. `Streaming/Channels/101`
   veya markaya göre `stream1`, `live/ch0` vb. — kameranızın RTSP URI'sini üreticisinin
   belgelerinden kontrol edin), kullanıcı adı ve parolayı girin.
2. **Bağlantıyı Test Et** ile gerçek bir kare alınabildiğini doğrulayın.
3. Kaydedin. Kamera etkinse arka planda otomatik olarak bağlanmaya başlar ve
   "Canlı İzleme" ekranında görüntülenir.

Parola veritabanına **yazılmaz**; `keyring` üzerinden Windows Credential
Manager'a kaydedilir. RTSP URL'si (parola dahil) hiçbir zaman log dosyasına
yazılmaz — yalnızca kamera adı/host loglanır.

Varsayılan olarak RTSP TCP taşıma kullanılır (Ayarlar ekranından UDP'ye
değiştirilebilir).

## Demo/Test Modu

Gerçek bir RTSP kameranız yoksa, kamera ekleme diyaloğunda **"Demo/Test
kaynağı kullan"** kutusunu işaretleyin. Bu, üzerinde gerçek bir plaka
metninin ("34 ABC 123") render edildiği yerel bir test videosu
(`assets/demo/demo_plates.avi`, ilk kullanımda otomatik oluşturulur) döngüsel
olarak oynatır. **Önemli:** bu modda sahte bir tespit sonucu enjekte
edilmez — video karesi, gerçek Haar cascade + gerçek Tesseract OCR motorundan
geçer; motor plakayı okuyamazsa kayıt da oluşmaz.

## Varsayılan Giriş Bilgileri

```
Kullanıcı adı: admin
Parola: admin123
```

İlk girişten sonra bu parolayı değiştirmeniz şiddetle önerilir (şu anki
sürümde parola değiştirme arayüzü yoktur; `users` tablosunu
`app/services/auth_service.hash_password` kullanarak güncelleyebilir veya
bir sonraki sürümde eklenecek "Kullanıcı Yönetimi" ekranını bekleyebilirsiniz
— bkz. Bilinen Kısıtlar).

## Testler

```
pip install -r requirements-build.txt
pytest -q
```

Testler; plaka normalizasyonu/doğrulama, veritabanı repository'leri (CRUD,
tekillik kısıtları), kimlik bilgisi deposu (fallback), parola hashleme/giriş,
saklama süresi temizliği ve CSV dışa aktarmayı kapsar. Kamera/OCR gibi
donanım veya sistem ikilisi (Tesseract) gerektiren bileşenler, birim
testlerinde doğrudan test edilmez (bunlar için "Bağlantıyı Test Et" ve
Demo Modu kullanılır); bu, `tests/` dizininin kapsam dışında bıraktığı
bilinen bir sınırdır.

## EXE / Kurulum Paketi Üretimi

**Yalnızca Windows üzerinde çalıştırılabilir** (PyInstaller cross-compile
desteklemez).

```
build.bat
```

Bu script sırasıyla: bağımlılıkları kurar → testleri çalıştırır (başarısız
olursa derleme durur) → klasör tabanlı (onedir) EXE üretir → tek dosyalı
(onefile) EXE'yi dener → Inno Setup kuruluysa bir kurulum paketi (.exe) üretir.

Çıktılar:
- Klasör tabanlı: `dist\PlakaTanimaSistemi\PlakaTanimaSistemi.exe`
- Tek dosyalı (opsiyonel): `dist\PlakaTanimaSistemiOneFile.exe`
- Kurulum paketi (Inno Setup kuruluysa): `installer_output\PlakaTanimaSistemi_Setup.exe`

Tam bağımsız (Tesseract'ın hedef makinede ayrıca kurulmasını gerektirmeyen)
bir dağıtım için, derlemeden önce `vendor\tesseract\` klasörüne Tesseract-OCR
kurulumunuzun içeriğini (`tesseract.exe`, `tessdata\` vb.) kopyalayın;
uygulama açılışta bu klasörü otomatik algılar (`app/utils/tesseract_locator.py`).

## Sorun Giderme

| Belirti | Olası Neden / Çözüm |
|---|---|
| "Tanıma motoru başlatılamadı" | OpenCV kurulumu bozuk; `pip install --force-reinstall opencv-python-headless` |
| "Tesseract OCR motoru bulunamadı" | Tesseract kurulu değil veya PATH'te değil; kurulum adımı 2'yi tekrarlayın veya `vendor\tesseract` kullanın |
| Kamera "Hata" durumunda kalıyor | RTSP URL/port/kimlik bilgisi hatalı olabilir; "Bağlantı Testi" ile doğrulayın; kameranın TCP RTSP'yi desteklediğinden emin olun (bazı eski kameralar yalnızca UDP destekler — Ayarlar'dan değiştirin) |
| Canlı görüntü donuk/gecikmeli | Çok sayıda kamera + CPU tabanlı tespit/OCR darboğazı olabilir (bkz. Bilinen Kısıtlar) |
| Plakalar hep "incelemeye" düşüyor | Ayarlar'dan güven eşiklerini düşürün; kamera açısı/çözünürlüğünü iyileştirin; Haar cascade genel amaçlıdır, her açıdan mükemmel çalışmaz |

## Bilinen Kısıtlar

- **Haar cascade tabanlı tespit**, derin öğrenme tabanlı (YOLO vb.) çözümlere
  göre daha düşük doğruluk sağlar; özellikle açılı, uzak veya düşük ışıklı
  plakalarda kaçırma/yanlış pozitif oranı yüksek olabilir.
- **CPU tabanlı işleme**: GPU hızlandırma yoktur; çok sayıda eş zamanlı
  kamera + yüksek FPS hedefinde gecikme oluşabilir (tasarım gereği, her
  kamera için yalnızca "en son kare" işlenir — bkz. `app/camera/frame_store.py`).
  Üretimde yüksek kamera sayısı için kamera başına ayrı işlem/iş parçacığı
  havuzu eklenmesi önerilir.
- **Kullanıcı yönetimi arayüzü yok**: `users` tablosu ve `AuthService` hazır,
  ancak UI'da yalnızca giriş ekranı var; kullanıcı ekleme/parola değiştirme
  ekranı bir sonraki adımdır.
- **Excel (.xlsx) dışa aktarma yok**: Yalnızca CSV (Excel'de doğrudan
  açılabilir, UTF-8 BOM ile). Gerekirse `app/services/export_service.py`
  yanına `openpyxl` tabanlı ayrı bir modül eklenebilir.
- **Fiziksel bariyer entegrasyonu yok** (kasıtlı — istenmedi); yetkili
  araç eşleştirme sonucu yalnızca arayüzde gösterilir.
- **Bu proje Linux geliştirme ortamında yazılmış ve test edilmiştir**
  (PySide6/OpenCV/SQLite Linux'ta da çalışır); Windows'a özgü davranışlar
  (Credential Manager, EXE/installer üretimi) Windows'ta ayrıca
  doğrulanmalıdır — bkz. proje raporu.

## Mimari

```
main.py                     Uygulama giriş noktası
app/
  config/                   Sabitler, yol çözümleme, çalışma zamanı ayarları
  database/                 Şema, migrasyonlar, bağlantı, repository'ler, modeller
  camera/                   RTSP worker (QThread), kamera yöneticisi, frame buffer,
                             bağlantı testi, demo video üretici
  recognition/               Plaka tespiti (Haar), OCR (Tesseract), pipeline
  services/                 AppContext (kompozisyon kökü), tanıma servisi,
                             auth, retention, CSV export
  utils/                    Plaka normalizasyon/doğrulama, kimlik bilgisi deposu,
                             loglama, tesseract yol çözümleme
  ui/                       PySide6 arayüzü (ekranlar, diyaloglar, widget'lar, tema)
models/                     (Haar cascade OpenCV paketinden çalışma zamanında okunur)
assets/                     Demo video, ikonlar
tests/                      pytest birim testleri
```
