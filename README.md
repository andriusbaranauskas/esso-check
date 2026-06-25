# ESO Free Capacity Check

Home Assistant custom integration (HACS) that checks [ESO laisvos galios pasitikrinimas](https://www.eso.lt/namams/gaminantis-vartotojas/laisvos-galios-pasitikrinimas/362) for your object number once per day.

## What it does

1. Loads the ESO check page and obtains a session token.
2. Posts your **object number** (for example `17055591`) to the ESO API.
3. Parses the response:
   - If the text contains **"Laisvos galios pastotėje nėra"** → sensor state is `none`
   - Otherwise → sensor state is `true`

A binary sensor is also provided for automations:

- `on` = free capacity available
- `off` = no free capacity at the substation

## Installation (HACS)

1. Add this repository as a custom HACS repository.
2. Install **ESO Free Capacity Check**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration**.
5. Search for **ESO Free Capacity Check**.
6. Enter your 8-digit object number.

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| Object number | required | Your ESO object number (up to 8 digits) |
| Check URL | ESO page URL | Override only if ESO changes the page path |
| Scan interval | `86400` (24 h) | How often to poll ESO, in seconds |

## Entities

| Entity | Example state | Meaning |
|--------|---------------|---------|
| `sensor.eso_<number>_free_capacity` | `true` / `none` | Text sensor matching your requested values |
| `binary_sensor.eso_<number>_free_capacity_available` | `on` / `off` | Easier for automations |

Both entities expose attributes:

- `message` – first ESO response message
- `messages` – all ESO messages
- `capacities` – `LOG`, `IGG`, `LGG` values when returned
- `object_number`

## Example automation

```yaml
automation:
  - alias: Notify when ESO free capacity appears
    trigger:
      - platform: state
        entity_id: sensor.eso_17055591_free_capacity
        to: "true"
    action:
      - service: notify.mobile_app
        data:
          message: "ESO reports free capacity at your substation."
```

## Manual install

Copy `custom_components/eso_check` into your Home Assistant `config/custom_components/` directory and restart Home Assistant.
