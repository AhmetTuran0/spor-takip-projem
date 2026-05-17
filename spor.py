import sqlite3
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)


# --- VERI MERKEZI (Şablon Yapı Güncellendi) ---
class VeriDeposu:
    uyeler = []
    sporlar = []


# --- VERİTABANI YARDIMCI FONKSİYONLARI ---
def veritabani_hazirla():
    """Program ilk açıldığında veritabanını ve yeni sütunlarla tabloları hazırlar."""
    conn = sqlite3.connect("fitpro_v3.db")  # Versiyon çakışması olmaması için DB adı güncellendi
    cursor = conn.cursor()

    # Üyeler Tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS uyeler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT,
            boy TEXT,
            kilo TEXT,
            vki TEXT
        )
    """
    )

    # Geliştirilmiş Sporlar/Egzersizler Tablosu (Set, Tekrar ve Süre Eklendi)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sporlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad TEXT,
            kalori TEXT,
            set_sayisi TEXT,
            tekrar_sayisi TEXT,
            sure TEXT
        )
    """
    )

    # Antrenman Programları Tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS antrenmanlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uye_id INTEGER,
            spor_ad TEXT
        )
    """
    )

    # Varsayılan Üyeler
    cursor.execute("SELECT COUNT(*) FROM uyeler")
    if cursor.fetchone()[0] == 0:
        varsayilan_uyeler = [
            ("Ahmet Turan", "180", "80", "24.7"),
            ("Ayşe Yılmaz", "165", "55", "20.2"),
            ("Mehmet Demir", "175", "90", "29.4"),
        ]
        cursor.executemany(
            "INSERT INTO uyeler (ad, boy, kilo, vki) VALUES (?, ?, ?, ?)",
            varsayilan_uyeler,
        )

    # GENİŞLETİLMİŞ HAREKET ENVANTERİ (Set, Tekrar ve Süre Detaylarıyla)
    cursor.execute("SELECT COUNT(*) FROM sporlar")
    if cursor.fetchone()[0] == 0:
        varsayilan_sporlar = [
            # Kardiyo & Dayanıklılık
            ("Koşu Bandı (Kardiyo)", "450", "1", "1", "30 dk"),
            ("Yüzme (Tüm Vücut)", "400", "1", "1", "45 dk"),
            ("Bisiklet (Kardiyo)", "300", "1", "1", "20 dk"),
            # Göğüs & Kol
            ("Bench Press (Göğüs)", "180", "4", "10", "—"),
            ("Incline Dumbbell Press", "160", "4", "12", "—"),
            ("Biceps Curl (Ön Kol)", "120", "3", "12", "—"),
            ("Triceps Pushdown (Arka Kol)", "110", "3", "15", "—"),
            # Sırt & Omuz
            ("Lat Pulldown (Sırt)", "150", "4", "10", "—"),
            ("Seated Cable Row (Sırt)", "140", "4", "12", "—"),
            ("Overhead Shoulder Press", "160", "4", "10", "—"),
            # Bacak & Karın
            ("Squat (Bacak)", "220", "4", "12", "—"),
            ("Leg Press (Bacak)", "190", "4", "10", "—"),
            ("Plank (Karın)", "80", "3", "1", "1 dk"),
            ("Mekik / Crunch (Karın)", "90", "3", "20", "—")
        ]
        cursor.executemany(
            "INSERT INTO sporlar (ad, kalori, set_sayisi, tekrar_sayisi, sure) VALUES (?, ?, ?, ?, ?)",
            varsayilan_sporlar
        )

    conn.commit()
    conn.close()


def verileri_veritabanindan_yukle():
    """Veritabanındaki güncel verileri çekip sistem hafızasına yükler."""
    conn = sqlite3.connect("fitpro_v3.db")
    cursor = conn.cursor()

    # Spor Kataloğunu Yeni Detaylarla Yükle
    cursor.execute("SELECT ad, kalori, set_sayisi, tekrar_sayisi, sure FROM sporlar")
    VeriDeposu.sporlar = [
        {
            "ad": row[0], 
            "kalori": row[1], 
            "set_sayisi": row[2], 
            "tekrar_sayisi": row[3], 
            "sure": row[4]
        } for row in cursor.fetchall()
    ]

    # Üyeleri ve Programlarını Yükle
    VeriDeposu.uyeler = []
    cursor.execute("SELECT id, ad, boy, kilo, vki FROM uyeler")
    tum_uyeler = cursor.fetchall()

    for u_id, ad, boy, kilo, vki in tum_uyeler:
        cursor.execute("SELECT spor_ad FROM antrenmanlar WHERE uye_id = ?", (u_id,))
        uye_antrenmanlari = [row[0] for row in cursor.fetchall()]

        VeriDeposu.uyeler.append(
            {
                "id": u_id,
                "ad": ad,
                "boy": boy,
                "kilo": kilo,
                "vki": vki,
                "antrenmanlar": uye_antrenmanlari,
            }
        )

    conn.close()


# --- ADMİN GİRİŞ EKRANI ---
class GirisEkrani(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FitPro | Yönetim Girişi")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.container = QFrame(self)
        self.container.setGeometry(10, 10, 380, 480)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #1e272e;
                border-radius: 20px;
                border: 2px solid #34495e;
            }
        """)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(30, 40, 30, 40)

        lbl_head = QLabel("FITPRO\nGİRİŞ")
        lbl_head.setStyleSheet("color: #f1c40f; font-size: 32px; font-weight: bold; margin-bottom: 20px;")
        lbl_head.setAlignment(Qt.AlignCenter)

        input_style = """
            QLineEdit {
                padding: 12px;
                background: #2f3542;
                color: white;
                border: 1px solid #57606f;
                border-radius: 8px;
                font-size: 14px;
            }
            QLineEdit:focus { border: 1px solid #f1c40f; }
        """
        self.a_user = QLineEdit(placeholderText="Yönetici Kullanıcı Adı")
        self.a_pass = QLineEdit(placeholderText="Şifre")
        self.a_pass.setEchoMode(QLineEdit.Password)
        self.a_user.setStyleSheet(input_style)
        self.a_pass.setStyleSheet(input_style)

        btn_login = QPushButton("SİSTEME GİRİŞ YAP")
        btn_login.setStyleSheet("""
            QPushButton {
                background: #f1c40f; color: #1e272e; font-weight: bold; 
                padding: 15px; border-radius: 8px; font-size: 14px;
            }
            QPushButton:hover { background: #e1b100; }
        """)
        btn_login.clicked.connect(self.admin_check)

        btn_exit = QPushButton("Kapat")
        btn_exit.setStyleSheet("color: #7f8c8d; border: none; margin-top: 10px;")
        btn_exit.clicked.connect(self.reject)

        layout.addWidget(lbl_head)
        layout.addStretch()
        layout.addWidget(self.a_user)
        layout.addWidget(self.a_pass)
        layout.addWidget(btn_login)
        layout.addWidget(btn_exit)
        layout.addStretch()

    def admin_check(self):
        if self.a_user.text() == "admin" and self.a_pass.text() == "admin":
            self.accept()
        else:
            QMessageBox.critical(self, "Hata", "Geçersiz Yönetici Bilgileri!")


# --- ANA YÖNETİM PANELİ ---
class FitnessAdminPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FitPro v3.0 | Gelişmiş Yönetim Paneli")
        self.resize(1300, 850)
        self.setStyleSheet("background-color: #f1f2f6;")
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(280)
        sidebar.setStyleSheet("background: #1e272e;")
        s_lay = QVBoxLayout(sidebar)

        lbl_logo = QLabel("FITPRO\nMASTER")
        lbl_logo.setStyleSheet("color:#f1c40f; font-size:26px; font-weight:bold; margin:40px 0;")
        lbl_logo.setAlignment(Qt.AlignCenter)

        btn_style = """
            QPushButton {
                color: white; text-align: left; padding: 15px 25px;
                border: none; font-size: 15px; font-weight: 500;
            }
            QPushButton:hover { background: #2f3542; color: #f1c40f; }
        """
        self.btn_uye_sayfa = QPushButton("👤 Üye Yönetimi")
        self.btn_spor_sayfa = QPushButton("🏋️ Hareket Listesi")
        self.btn_uye_sayfa.setStyleSheet(btn_style)
        self.btn_spor_sayfa.setStyleSheet(btn_style)

        btn_logout = QPushButton("🚪 Oturumu Kapat")
        btn_logout.setStyleSheet("color:#ff4757; border:none; font-weight:bold; padding:30px; text-align:left;")
        btn_logout.clicked.connect(self.logout)

        s_lay.addWidget(lbl_logo)
        s_lay.addWidget(self.btn_uye_sayfa)
        s_lay.addWidget(self.btn_spor_sayfa)
        s_lay.addStretch()
        s_lay.addWidget(btn_logout)

        main_layout.addWidget(sidebar)
        self.stack = QStackedWidget()

        # SAYFA 1: ÜYE YÖNETİMİ
        self.page_uye = QWidget()
        uye_lay = QVBoxLayout(self.page_uye)
        uye_lay.setContentsMargins(40, 40, 40, 40)

        h1 = QLabel("Üye ve Antrenman Atama")
        h1.setStyleSheet("font-size: 28px; font-weight: bold; color: #2d3436; margin-bottom: 20px;")

        form_uye = QHBoxLayout()
        self.in_uye_ad = QLineEdit(placeholderText="Yeni Üye Adı Soyadı")
        self.in_uye_boy = QLineEdit(placeholderText="Boy (cm)")
        self.in_uye_kilo = QLineEdit(placeholderText="Kilo (kg)")

        style_input = "padding:15px; border-radius:10px; border:1px solid #ced4da; background:white;"
        self.in_uye_ad.setStyleSheet(style_input)
        self.in_uye_boy.setStyleSheet(style_input)
        self.in_uye_kilo.setStyleSheet(style_input)

        btn_add_uye = QPushButton("ÜYE EKLE")
        btn_add_uye.setStyleSheet("background:#2ecc71; color:white; font-weight:bold; padding:15px 30px; border-radius:10px;")
        btn_add_uye.clicked.connect(self.uye_ekle)

        form_uye.addWidget(self.in_uye_ad)
        form_uye.addWidget(self.in_uye_boy)
        form_uye.addWidget(self.in_uye_kilo)
        form_uye.addWidget(btn_add_uye)

        self.list_uyeler = QListWidget()
        self.list_uyeler.setStyleSheet("border-radius:15px; padding:10px; border:none; background:white; font-size:15px;")

        btn_ata = QPushButton("SEÇİLİ ÜYEYE ANTRENMAN ATA")
        btn_ata.setStyleSheet("background:#1e272e; color:white; font-weight:bold; padding:15px; border-radius:10px; margin-top:10px;")
        btn_ata.clicked.connect(self.antrenman_ata)

        uye_lay.addWidget(h1)
        uye_lay.addLayout(form_uye)
        uye_lay.addWidget(QLabel("<b>Kayıtlı Üyeler ve Detaylı Programları</b>", styleSheet="margin-top:20px; color:#636e72;"))
        uye_lay.addWidget(self.list_uyeler)
        uye_lay.addWidget(btn_ata)

        # SAYFA 2: SPOR YÖNETİMİ (Yeni Alanlar Eklendi)
        self.page_spor = QWidget()
        spor_lay = QVBoxLayout(self.page_spor)
        spor_lay.setContentsMargins(40, 40, 40, 40)

        h2 = QLabel("Egzersiz Kataloğu Yönetimi")
        h2.setStyleSheet("font-size: 28px; font-weight: bold; color: #2d3436; margin-bottom: 20px;")

        # Form düzeni yeni girdilere göre genişletildi
        form_spor = QHBoxLayout()
        self.in_spor_ad = QLineEdit(placeholderText="Hareket Adı")
        self.in_spor_kal = QLineEdit(placeholderText="Kalori (kcal/s)")
        self.in_spor_set = QLineEdit(placeholderText="Set Sayısı")
        self.in_spor_tekrar = QLineEdit(placeholderText="Tekrar Sayısı")
        self.in_spor_sure = QLineEdit(placeholderText="Süre (Örn: 30 dk / —)")

        style_spor = "padding:12px; border-radius:8px; border:1px solid #ced4da; background:white;"
        self.in_spor_ad.setStyleSheet(style_spor)
        self.in_spor_kal.setStyleSheet(style_spor)
        self.in_spor_set.setStyleSheet(style_spor)
        self.in_spor_tekrar.setStyleSheet(style_spor)
        self.in_spor_sure.setStyleSheet(style_spor)

        btn_add_spor = QPushButton("EGZERSİZ EKLE")
        btn_add_spor.setStyleSheet("background:#f1c40f; color:#1e272e; font-weight:bold; padding:12px 20px; border-radius:8px;")
        btn_add_spor.clicked.connect(self.spor_ekle)

        form_spor.addWidget(self.in_spor_ad)
        form_spor.addWidget(self.in_spor_kal)
        form_spor.addWidget(self.in_spor_set)
        form_spor.addWidget(self.in_spor_tekrar)
        form_spor.addWidget(self.in_spor_sure)
        form_spor.addWidget(btn_add_spor)

        self.list_sporlar = QListWidget()
        self.list_sporlar.setStyleSheet("border-radius:15px; padding:10px; border:none; background:white; font-size:15px;")

        spor_lay.addWidget(h2)
        spor_lay.addLayout(form_spor)
        spor_lay.addWidget(QLabel("<b>Sistemdeki Gelişmiş Hareket Envanteri</b>", styleSheet="margin-top:20px; color:#636e72;"))
        spor_lay.addWidget(self.list_sporlar)

        self.stack.addWidget(self.page_uye)
        self.stack.addWidget(self.page_spor)
        main_layout.addWidget(self.stack)

        self.btn_uye_sayfa.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_spor_sayfa.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        self.verileri_yukle()

    def verileri_yukle(self):
        verileri_veritabanindan_yukle()

        # Detayları kullanıcı arayüzünde düzgün eşleştirmek için bir harita oluşturuyoruz
        spor_detay_map = {}
        for s in VeriDeposu.sporlar:
            set_t = f"{s['set_sayisi']}S" if s['set_sayisi'] != "—" else ""
            tek_t = f"x{s['tekrar_sayisi']}T" if s['tekrar_sayisi'] != "—" else ""
            sure_t = f" ({s['sure']})" if s['sure'] != "—" else ""
            
            detay_str = f"{s['ad']}"
            if set_t or tek_t or sure_t:
                detay_str += f" [{set_t}{tek_t}{sure_t}]"
            spor_detay_map[s['ad']] = detay_str

        # Üye listesini güncelleme
        self.list_uyeler.clear()
        for u in VeriDeposu.uyeler:
            prog_list = [spor_detay_map.get(ant, ant) for ant in u["antrenmanlar"]]
            prog = ", ".join(prog_list) if prog_list else "Program yok"
            boy = u.get("boy", "-")
            kilo = u.get("kilo", "-")
            vki = u.get("vki", "-")
            self.list_uyeler.addItem(
                f"👤 {u['ad']}  [Boy: {boy} cm | Kilo: {kilo} kg | VKİ: {vki}]\n 📋 Program: {prog}\n"
            )

        # Spor listesini güncelleme (Gelişmiş Görünüm)
        self.list_sporlar.clear()
        for s in VeriDeposu.sporlar:
            set_bilgi = f"{s['set_sayisi']} Set" if s['set_sayisi'] else "—"
            tekrar_bilgi = f"{s['tekrar_sayisi']} Tekrar" if s['tekrar_sayisi'] else "—"
            sure_bilgi = f"Süre: {s['sure']}" if s['sure'] and s['sure'] != "—" else ""
            
            parametreler = f"[{set_bilgi} x {tekrar_bilgi}"
            if sure_bilgi:
                parametreler += f" | {sure_bilgi}]"
            else:
                parametreler += "]"
                
            self.list_sporlar.addItem(f"🔥 {s['ad']} — {s['kalori']} kcal/s   {parametreler}")

    def uye_ekle(self):
        ad = self.in_uye_ad.text().strip()
        boy_txt = self.in_uye_boy.text().strip()
        kilo_txt = self.in_uye_kilo.text().strip()

        if ad and boy_txt and kilo_txt:
            try:
                boy_cm = float(boy_txt)
                kilo_kg = float(kilo_txt)
                vki_hesap = kilo_kg / ((boy_cm / 100) ** 2)
                vki_str = f"{vki_hesap:.1f}"

                conn = sqlite3.connect("fitpro_v3.db")
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO uyeler (ad, boy, kilo, vki) VALUES (?, ?, ?, ?)",
                    (ad, boy_txt, kilo_txt, vki_str),
                )
                conn.commit()
                conn.close()

                self.verileri_yukle()
                self.in_uye_ad.clear()
                self.in_uye_boy.clear()
                self.in_uye_kilo.clear()
            except ValueError:
                QMessageBox.warning(self, "Hata", "Boy ve Kilo alanlarına geçerli sayısal değerler giriniz!")
        else:
            QMessageBox.warning(self, "Hata", "Lütfen isim, boy ve kilo bilgilerini eksiksiz doldurunuz!")

    def antrenman_ata(self):
        index = self.list_uyeler.currentRow()
        if index >= 0:
            spor_listesi = [s["ad"] for s in VeriDeposu.sporlar]
            if not spor_listesi:
                QMessageBox.warning(self, "Hata", "Sistemde egzersiz bulunmuyor!")
                return

            secim, ok = QInputDialog.getItem(
                self,
                "Antrenman Ata",
                f"{VeriDeposu.uyeler[index]['ad']} için hareket seçin:",
                spor_listesi,
                0,
                False,
            )
            if ok and secim:
                if secim not in VeriDeposu.uyeler[index]["antrenmanlar"]:
                    uye_id = VeriDeposu.uyeler[index]["id"]

                    conn = sqlite3.connect("fitpro_v3.db")
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO antrenmanlar (uye_id, spor_ad) VALUES (?, ?)",
                        (uye_id, secim),
                    )
                    conn.commit()
                    conn.close()

                    self.verileri_yukle()
                else:
                    QMessageBox.information(self, "Bilgi", "Bu hareket zaten programda mevcut.")
        else:
            QMessageBox.warning(self, "Hata", "Lütfen bir üye seçin!")

    def spor_ekle(self):
        """Yeni eklenen parametrelerle birlikte egzersizi veritabanına kaydeder."""
        ad = self.in_spor_ad.text().strip()
        kal = self.in_spor_kal.text().strip()
        set_sayisi = self.in_spor_set.text().strip() or "—"
        tekrar = self.in_spor_tekrar.text().strip() or "—"
        sure = self.in_spor_sure.text().strip() or "—"

        if ad and kal:
            conn = sqlite3.connect("fitpro_v3.db")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sporlar (ad, kalori, set_sayisi, tekrar_sayisi, sure) VALUES (?, ?, ?, ?, ?)",
                (ad, kal, set_sayisi, tekrar, sure),
            )
            conn.commit()
            conn.close()

            self.verileri_yukle()
            
            # Girdi alanlarını temizleme
            self.in_spor_ad.clear()
            self.in_spor_kal.clear()
            self.in_spor_set.clear()
            self.in_spor_tekrar.clear()
            self.in_spor_sure.clear()
        else:
            QMessageBox.warning(self, "Hata", "Egzersiz adı ve kalori bilgisini girmek zorunludur!")

    def logout(self):
        self.close()
        main()


def main():
    veritabani_hazirla()
    login = GirisEkrani()
    if login.exec_() == QDialog.Accepted:
        global panel
        panel = FitnessAdminPanel()
        panel.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    main()
    sys.exit(app.exec_())