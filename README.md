# RFID Access Control Integration

Sistema completo di controllo accesso basato su PIN + RFID per Home Assistant.

Compatibile con: **KEPZB-110** (Frient Keypad Zigbee)

## ✨ Caratteristiche

- 🔐 **Doppia autenticazione** PIN + RFID per ogni utente
- 👥 **Gestione dinamica utenti** (aggiungi/elimina)
- ⚡ **Azioni personalizzate** per ogni utente (luci, porte, automazioni)
- 🎮 **Card Lovelace intuitiva** per gestire tutto
- 💾 **Database persistente** in local storage
- 📊 **Tracciamento accessi** per utente
- 🔄 **Webhook ready** per integrazioni esterne
- ✅ **Auto-riconoscimento device Zigbee**

## 📦 Installazione

### 1. Download integrazione

```bash
git clone https://github.com/yourusername/rfid-access-control
```

### 2. Copia in Home Assistant

```bash
# Via SSH o SFTP
cp -r rfid-access-control/custom_components/rfid_access_control /config/custom_components/
```

### 3. Riavvia Home Assistant

Impostazioni → Sistema → Riavvia Home Assistant

### 4. Aggiungi integrazione

- Impostazioni → Dispositivi e Servizi
- **+ AGGIUNGI INTEGRAZIONE**
- Cerca "**RFID Access Control**"
- Seleziona il tuo tastierino KEPZB-110

## 🎮 Setup Card Lovelace

### 1. Registra risorsa

**Impostazioni** → **Dashboard** → **⋮** → **Risorse**

- URL: `/local/community/rfid-access-control/rfid-access-control-card.js`
- Tipo: **JavaScript Module**

### 2. Aggiungi card dashboard

```yaml
type: custom:rfid-access-control-card
title: RFID Access Control
entity: "climate.home"  # Entity per visibilità
```

## 📋 Utilizzo

### Aggiungi utente via card

1. Click **+ Add User**
2. Compila:
   - User ID: `mario_001`
   - Full Name: `Mario Rossi`
   - PIN: `1234` (opzionale)
   - RFID: `04A12B3C` (opzionale)
3. Click **Create User**

### Aggiungi azioni per utente

1. Click **Edit** su utente
2. Click **⚙️ Manage Actions**
3. Configura azione:
   - Action Name: `Open Front Door`
   - Entity ID: `lock.front_door`
   - Service: `lock.unlock`
   - Service Data: `{"code": "1234"}`
4. Click **Add Action**

### Validare accesso

Quando utente inserisce PIN + RFID (o uno solo):

```yaml
service: rfid_access_control.validate_access
data:
  user_pin: "1234"
  user_rfid: "04A12B3C"
```

**Risultato:**
- ✅ Credenziali valide → Esegui tutte le azioni dell'utente
- ❌ Credenziali non valide → Evento `rfid_access_denied`

## 🔧 Servizi Disponibili

### `rfid_access_control.add_user`

Aggiungi nuovo utente

```yaml
service: rfid_access_control.add_user
data:
  user_id: mario_001
  user_name: Mario Rossi
  user_pin: "1234"
  user_rfid: "04A12B3C"
```

### `rfid_access_control.remove_user`

Elimina utente

```yaml
service: rfid_access_control.remove_user
data:
  user_id: mario_001
```

### `rfid_access_control.update_user`

Modifica utente

```yaml
service: rfid_access_control.update_user
data:
  user_id: mario_001
  user_name: Mario Rossi Updated
  enabled: true
```

### `rfid_access_control.validate_access`

Valida credenziali ed esegui azioni

```yaml
service: rfid_access_control.validate_access
data:
  user_pin: "1234"
  user_rfid: "04A12B3C"
```

### `rfid_access_control.add_action`

Aggiungi azione a utente

```yaml
service: rfid_access_control.add_action
data:
  user_id: mario_001
  action_name: "Open Front Door"
  action_entity: lock.front_door
  action_service: lock.unlock
  action_data: {"code": "1234"}
```

### `rfid_access_control.remove_action`

Rimuovi azione da utente

```yaml
service: rfid_access_control.remove_action
data:
  user_id: mario_001
  action_name: "Open Front Door"
```

## 📡 Eventi Disponibili

### `rfid_access_granted`

Accesso concesso

```
rfid_access_granted:
  user_id: mario_001
  user_name: Mario Rossi
```

### `rfid_access_denied`

Accesso negato

```
rfid_access_denied:
  pin: "***"
  rfid: "A12B"
```

### `rfid_user_added`

Utente aggiunto

### `rfid_user_removed`

Utente rimosso

## 🎯 Esempi di Automazioni

### Invia notifica su accesso

```yaml
automation:
  - alias: "RFID - Notify Access"
    trigger:
      - platform: event
        event_type: rfid_access_granted
    action:
      - service: notify.notify
        data:
          message: "{{ trigger.event.data.user_name }} has accessed the door"
```

### Accendi luce al riconoscimento

```yaml
automation:
  - alias: "RFID - Light On"
    trigger:
      - platform: event
        event_type: rfid_access_granted
    action:
      - service: light.turn_on
        target:
          entity_id: light.entrance
        data:
          brightness: 255
          transition: 0
```

### Log negata

```yaml
automation:
  - alias: "RFID - Log Access Denied"
    trigger:
      - platform: event
        event_type: rfid_access_denied
    action:
      - service: system_log.write
        data:
          message: "RFID Access Denied - PIN: {{ trigger.event.data.pin }}"
          level: warning
```

## 🔗 Integrazione Tastierino KEPZB-110

Il tastierino comunica con Home Assistant via Zigbee (ZHA).

Per integrare con questa soluzione, crea un'automazione che cattura gli input:

```yaml
automation:
  - alias: "RFID - Process Keypad Input"
    trigger:
      - platform: event
        event_type: zha_event
        event_data:
          device_id: "YOUR_KEYPAD_ID"
    action:
      - service: rfid_access_control.validate_access
        data:
          user_pin: "{{ trigger.event.data.args[0] }}"
```

## 📁 Struttura Database

Gli utenti sono salvati in:

```
/config/rfid_access_control/{device_id}.json
```

Formato:

```json
{
  "user_001": {
    "user_id": "user_001",
    "user_name": "Mario Rossi",
    "pin": "1234",
    "rfid": "04A12B3C",
    "enabled": true,
    "actions": [
      {
        "entity_id": "lock.front_door",
        "service": "lock.unlock",
        "service_data": {"code": "1234"},
        "action_name": "Open Front Door"
      }
    ],
    "created_at": "2024-01-01T10:00:00",
    "last_access": "2024-01-05T15:30:00",
    "access_count": 5
  }
}
```

## 🐛 Troubleshooting

### Tastierino non riconosciuto

1. Verifica que KEPZB-110 sia accoppiato con ZHA
2. Controlla che il modello sia esattamente "KEPZB-110"
3. Riavvia Home Assistant

### Azioni non si eseguono

1. Verifica che entity_id e service siano corretti
2. Verifica che gli ID siano in lowercase
3. Controlla i log di Home Assistant

### Database non si salva

1. Verifica permessi directory `/config/rfid_access_control/`
2. Assicurati che Home Assistant possa scrivere

## 📄 License

MIT License - Free and Open Source

## 🙏 Support

Per problemi, apri una issue su GitHub
