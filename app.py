# AGROLINDI RH 🚜

**AGROLINDI RH** është një sistem modern për menaxhimin e dyqaneve bujqësore (Agroshop). Aplikacioni menaxhon inventarin, shitjet (POS), furnizimet dhe librin e borxheve, i fuqizuar nga Inteligjenca Artificiale (Gemini AI).

![Status](https://img.shields.io/badge/Status-Active-success)
![Tech](https://img.shields.io/badge/Built%20With-React%20%7C%20Tailwind%20%7C%20Gemini%20AI-blue)

## 🌟 Veçoritë Kryesore

### 🛒 Pika e Shitjes (POS)
- **Kasa e Shpejtë:** Kërkim inteligjent dhe shtim i produkteve në shportë.
- **Menaxhimi i Borxheve:**
  - Regjistrimi i shitjeve me borxh.
  - **Pagesa të Pjesshme:** Mundësia për të paguar vetëm një pjesë të borxhit.
  - **Marrëveshjet:** Etiketim special për borxhet me marrëveshje.
  - **Alarme Vonese:** Tregon automatikisht ditët e vonesës së pagesës.
- **Raporti i Fitimit:** Llogaritje në kohë reale e fitimit neto (Shitje - Kosto).

### 📦 Inventari & Furnizimet
- **Stoku:** Gjurmim i sasisë, çmimit të blerjes dhe shitjes.
- **Sugjerime Inteligjente:** Fushat plotësohen automatikisht bazuar në historikun e mëparshëm.
- **Furnizimet:** Regjistrimi i hyrjeve të mallit me data dhe kosto specifike.

### 📊 Paneli & Raportet
- **Statistika:** Të ardhurat totale, porositë, dhe alarme për stok të ulët (< 5).
- **Grafikë:** Analizë vizuale e shitjeve javore dhe produkteve më të shitura.
- **Kalendari:** Raporte ditore dhe mujore të detajuara (Hyrje vs Dalje).

### 🤖 Asistenti AI (Google Gemini)
- Chatbot i integruar që njeh të dhënat e dyqanit tuaj.
- Mund ta pyesni: *"Cilat produkte po mbarojnë?"* ose *"Sa ishte xhiro sot?"*.

## 🛠️ Teknologjitë

- **Frontend:** React 19 (TypeScript)
- **Design:** Tailwind CSS
- **Icons:** Lucide React
- **Charts:** Recharts
- **AI:** Google GenAI SDK (`@google/genai`)
- **Database:** LocalStorage (Funksionon 100% Offline)

## 🚀 Instalimi

1. **Klono repozitorin**
   ```bash
   git clone https://github.com/USERNAME/agrolindi-rh.git
