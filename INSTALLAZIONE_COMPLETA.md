# 📘 Guida Installazione Completa RFID Access Control

Installazione passo-passo dell'integrazione di controllo accesso RFID + PIN.

---

## ⚠️ Prerequisiti

- ✅ Home Assistant OS o Supervised
- ✅ Tastierino KEPZB-110 accoppiato con ZHA
- ✅ Accesso SSH, File Editor o Samba

---

## 🎯 PASSO 1: Prepara il Tastierino KEPZB-110

### 1.1 Verifica accoppiamento ZHA

1. **Impostazioni** → **Dispositivi e Servizi**
2. Cerca **"ZHA"**
3. Controlla che KEPZB-110 sia nella lista dei device Zigbee
4. Annota il **Device ID** (servirà dopo)

Se non accoppiato:
1. **ZHA** → **+ Add Device**
2. Metti tastierino in modalità pair
3. Completa accoppiamento

### 1.2 Prova tastierino

1. Home Assistant → **Sviluppatori** → **Eventi**
2. Ascolta evento: `zha_event`
3. Premi un tasto sul tastierino
4. Dovresti vedere l'evento con i dati

---

## 📦 PASSO 2: Installazione Integrazione

### 2.1 Scarica integrazione

```bash
git clone https://github.com/yourusername/rfid-access-control
cd rfid-access-control
```

### 2.2 Copia via SSH

```bash
# Connettiti a Home Assistant via SSH
ssh homeassistant@192.168.1.100

# Copia file
cd /config
mkdir -p custom_components
cp -r /path/to/rfid-access-control/custom_components/rfid_access_control custom_components/
```

**Oppure via Samba:**
1. Connettiti a Samba share
2. Vai in `/config/custom_components/`
3. Carica cartella `rfid_access_control`

**Oppure via File Editor:**
1. Crea cartella: `/config/custom_components/rfid_access_control/`
2. Carica tutti i file uno per uno

### 2.3 Verifica struttura

La cartella deve avere:

```
/config/custom_components/rfid_access_control/
├── __init__.py
├── config_flow.py
├── const.py
├── manifest.json
├── models.py
├── services.yaml
├── strings.json
└── www/
    └── rfid-access-control-card.js
```

### 2.4 Riavvia Home Assistant

**Impostazioni** → **Sistema** → **Riavvia Home Assistant**

---

## ⚙️ PASSO 3: Configura Integrazione

### 3.1 Aggiungi integrazione

1. **Impostazioni** → **Dispositivi e Servizi**
2. Click **+ AGGIUNGI INTEGRAZIONE**
3. Cerca **"RFID Access Control"**
4. Click su risultato
5. Seleziona il tuo tastierino KEPZB-110
6. Click **CREA**

Se non trovi il tastierino:
- ✅ Verifica che sia accoppiato con ZHA
- ✅ Riavvia Home Assistant
- ✅ Verifica che il modello sia esattamente "KEPZB-110"

---

## 🎨 PASSO 4: Registra Card Lovelace

### 4.1 Copia file card

Copia file da:
```
rfid-access-control/custom_components/rfid_access_control/www/rfid-access-control-card.js
```

A:
```
/config/www/rfid-access-control-card.js
```

Se la cartella `/config/www` non esiste, creala.

### 4.2 Registra risorsa Lovelace

1. **Impostazioni** → **Dashboard**
2. Click **⋮** (menu in alto a destra)
3. Click **Risorse**
4. Click **+ AGGIUNGI RISORSA**

Configurazione:
- **URL**: `/local/rfid-access-control-card.js`
- **Tipo**: **JavaScript Module**

5. Click **CREA**

### 4.3 Ricarica browser

- **CTRL + F5** (Windows/Linux)
- **CMD + SHIFT + R** (Mac)

---

## 🎮 PASSO 5: Aggiungi Card Dashboard

### 5.1 Modifica dashboard

1. Apri dashboard dove vuoi aggiungere card
2. Click **⋮** → **Modifica Dashboard**
3. Click **+ AGGIUNGI CARD**

### 5.2 Cerca card

1. **Manuale** → Scorri fino in fondo
2. **Ricerca** → Digita "RFID"
3. Seleziona **"RFID Access Control Card"**

### 5.3 Configurazione card

```yaml
type: custom:rfid-access-control-card
title: RFID Access Control
entity: "climate.home"
```

4. Click **SALVA**

---

## 👥 PASSO 6: Aggiungi Primo Utente

### 6.1 Via Card Lovelace

1. Apri dashboard
2. Nella card RFID, click **+ Add User**
3. Compila form:
   - **User ID**: `mario_001` (no spazi)
   - **Full Name**: `Mario Rossi`
   - **PIN**: `1234` (opzionale, 4-8 cifre)
   - **RFID**: `04A12B3C` (opzionale)
4. Click **Create User**

### 6.2 Via Servizio (alternativa)

**Sviluppatori** → **Servizi**

Servizio: `rfid_access_control.add_user`

Dati:
```yaml
user_id: mario_001
user_name: Mario Rossi
user_pin: "1234"
user_rfid: "04A12B3C"
```

Click **CHIAMA SERVIZIO**

---

## 🚪 PASSO 7: Aggiungi Azione per Utente

### 7.1 Configura azione (esempio apertura porta)

1. Nella card RFID, click su **Edit** su utente
2. Click **⚙️ Manage Actions**
3. Compila:
   - **Action Name**: `Open Front Door`
   - **Target Entity**: `lock.front_door`
   - **Service**: `lock.unlock`
   - **Service Data**: (lascia vuoto o) `{"code": "1234"}`
4. Click **Add Action**

### 7.2 Verifiche

L'azione "Apri Porta" adesso:
- ✅ Si eseguirà quando Mario inserisce PIN 1234 + RFID
- ✅ Sbloccherà `lock.front_door`
- ✅ Registrerà l'accesso nel database

---

## 🔗 PASSO 8: Collegamento Tastierino (Automazione)

### 8.1 Crea automazione per leggere input tastierino

Apri `configuration.yaml` e aggiungi:

```yaml
automation:
  - alias: "RFID - Process Keypad Input"
    trigger:
      - platform: event
        event_type: zha_event
        event_data:
          device_id: "YOUR_DEVICE_ID"  # Sostituisci con ID KEPZB-110
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.args | length > 0 }}"
    action:
      - service: rfid_access_control.validate_access
        data:
          user_pin: "{{ trigger.event.data.args[0] }}"
```

### 8.2 Riavvia Home Assistant

**Impostazioni** → **Sistema** → **Riavvia**

### 8.3 Testa il flusso

1. Premi tasto PIN sul tastierino (es: 1234)
2. L'automazione dovrebbe intercettare l'input
3. Se PIN di Mario, la porta si apre!

---

## 📊 PASSO 9: Monitoraggio

### 9.1 Tracciamento accessi

Card RFID mostra per ogni utente:
- 📍 ID utente
- 🔑 PIN/RFID (mascherati)
- 📈 Numero accessi totali
- 🕐 Ultimo accesso

### 9.2 Eventi personalizzati

Crea automazioni su eventi RFID:

```yaml
automation:
  - alias: "RFID - Notify on Access"
    trigger:
      - platform: event
        event_type: rfid_access_granted
    action:
      - service: notify.notify
        data:
          title: "Accesso Concesso"
          message: "{{ trigger.event.data.user_name }} ha accesso"
```

---

## ✅ CHECKLIST INSTALLAZIONE

- [ ] Tastierino KEPZB-110 accoppiato con ZHA
- [ ] Integrazione RFID scaricata e copiata
- [ ] Home Assistant riavviato
- [ ] Integrazione aggiunta e configurata
- [ ] Card JS copiata in `/config/www/`
- [ ] Risorsa Lovelace registrata
- [ ] Card aggiunta a dashboard
- [ ] Primo utente creato
- [ ] Primo azione configurata
- [ ] Automazione tastierino creata

---

## 🐛 Troubleshooting

### Card non appare

**Soluzione:**
1. Verifica file `/config/www/rfid-access-control-card.js` esista
2. CTRL + F5 per ricaricare
3. Controlla console browser (F12) per errori

### Tastierino non riconosciuto

**Soluzione:**
1. Verifica che KEPZB-110 sia accoppiato ZHA
2. Riavvia Home Assistant
3. Verifica Device ID nel ZHA

### Azioni non si eseguono

**Soluzione:**
1. Verifica entity_id sia corretto (es: `lock.front_door`)
2. Verifica service sia corretto (es: `lock.unlock`)
3. Controlla logs Home Assistant

### Database non si salva

**Soluzione:**
1. Verifica permessi `/config/rfid_access_control/`
2. Assicurati Home Assistant possa scrivere
3. Controlla spazio disco

---

## 📚 Documentazione Completa

Vedi **README.md** per:
- Tutti i servizi disponibili
- Tutti gli eventi
- Esempi automazioni avanzate
- Integrazione esterna webhook

---

## 🎉 Installazione Completata!

Adesso puoi:
- ✅ Gestire utenti dinamicamente
- ✅ Assegnare azioni personalizzate
- ✅ Controllare porte e luci
- ✅ Tracciare accessi
- ✅ Creare automazioni avanzate

**Buon divertimento!** 🔐🚀
