# hass-control4 (forked)

This custom integration connects Home Assistant to a [Control4](https://www.control4.com/) home automation controller (Director), exposing the devices it manages as native Home Assistant entities. It supports lights, locks (relay-based locks only), alarm control panels, door/window/motion sensors (as binary sensors), thermostats, fans, relay devices (as switches), and blinds/shades (as covers, stateless open/close/stop), with live state updates pushed over a websocket connection to the Director rather than polling.

## Installation

### HACS Installation

This repo is **not** in the default HACS store. Add it as a custom repository first:

1. **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. Repository: `https://github.com/vemboy20/hass-control4`
3. Category: **Integration** → **Add**
4. **HACS** → **Integrations** → **Explore & Download Repositories** → find **Control4** → **Download**
5. **Restart Home Assistant**

Install the latest [release tag](https://github.com/vemboy20/hass-control4/releases) (stable). Pull requests merged into `release` publish a **pre-release drop** that you can install from HACS with **Show beta versions** enabled.

Once installed, follow the same setup instructions as the default integration: https://www.home-assistant.io/integrations/control4

If the HACS readme looks stale after an update: **HACS** → **⋮** → **Clear cache**, restart HA, then **Redownload** the integration.

### Prerequisites
Before setting up, you should assign a static IP address/DHCP reservation on your router to your Control4 controller. Home Assistant must be able to communicate with the controller over the local network; 4Sight remote access is not supported.

The username and password required for this integration are the same credentials you use to log in to the Control4 mobile app and the customer portal at [https://customer.control4.com/](https://customer.control4.com/).

### Configuration

Control4 can be autodiscovered, but if Home Assistant fails to discover it you can add it manually:

1. Browse to your Home Assistant instance.
2. Go to **Settings** → **Devices & Services**.
3. In the bottom right corner, select **Add Integration**.
4. Search for and select **Control4**.

| Parameter | Description |
| --------- | ----------- |
| IP address | IP address of your Control4 controller |
| Username | Username used to log in to the Control4 app / customer portal |
| Password | Password used to log in to the Control4 app / customer portal |

### Options

After setup, go to **Settings** → **Devices & Services** → **Control4** → **Configure** to adjust:

| Option | Description |
| ------ | ----------- |
| Alarm arm away mode name | Control4 arm mode that maps to HA "arm away" |
| Alarm arm home mode name | Control4 arm mode that maps to HA "arm home" |
| Alarm arm night mode name | Control4 arm mode that maps to HA "arm night" |
| Alarm arm vacation mode name | Control4 arm mode that maps to HA "arm vacation" |
| Alarm arm custom bypass mode name | Control4 arm mode that maps to HA "arm custom bypass" |
| Prepend device name to entity name | When enabled, entity names include the parent device name (e.g. "Lutron Switch Light") |

Set any alarm mode to `(not set)` if your system does not use that arming mode; the corresponding HA feature will be hidden.

**Example — DSC alarm panel:** set "Alarm arm home mode name" to `Stay` and "Alarm arm away mode name" to `Away`.


## Supported Devices and Functions

The integration maps Control4 device types to Home Assistant entity platforms as follows:

| Control4 Device | HA Platform | Supported Functions |
| --------------- | ----------- | ------------------- |
| Light switch / dimmer | `light` | On/off, brightness (1–100%), color temperature, XY color, transition time, effects |
| Fan | `fan` | On/off, speed percentage |
| Relay switch / pump | `switch` | On/off, toggle |
| Relay lock | `lock` | Lock, unlock |
| Security panel | `alarm_control_panel` | Arm away/home/night/vacation/custom bypass, disarm, trigger emergency |
| Door / window sensor | `binary_sensor` | Open/closed state |
| Motion sensor | `binary_sensor` | Motion detected/cleared |
| Thermostat | `climate` | Target temperature, HVAC mode (heat/cool/heat-cool/off), fan mode, preset |
| Blind / shade | `cover` | Open, close, stop, set position (on supported drivers) |
| Garage door | `cover` | Open, close, with open/closed state feedback |
| Media room / AV receiver | `media_player` | Play/pause/stop, volume up/down/mute, source selection, browse media, next/previous track |

Media player entities appear per Control4 room that has an audio or video endpoint configured in the Control4 project.

## Use Cases

- **Unified dashboard** — Control Control4 lights, thermostats, and blinds alongside devices from other ecosystems in a single Home Assistant dashboard.
- **Presence-based automation** — Turn off all Control4 lights or arm the security system automatically when everyone leaves home.
- **Voice control** — Use Home Assistant's Alexa or Google Home integrations to voice-control Control4 devices without a separate Control4 voice skill.
- **Advanced scenes** — Send arbitrary Control4 commands via the `control4.send_command` action to trigger Control4 experiences or scenes not directly exposed as HA entities.
- **Cross-system automations** — React to Control4 sensor state (door opened, motion detected) in automations that also control non-Control4 devices.

## Examples

### Turn off all lights when everyone leaves

```yaml
automation:
  alias: "Control4 – away lights off"
  trigger:
    - platform: state
      entity_id: zone.home
      to: "0"
  action:
    - service: light.turn_off
      target:
        area_id: living_room
```

### Arm the alarm when the last person leaves

```yaml
automation:
  alias: "Control4 – auto arm away"
  trigger:
    - platform: state
      entity_id: zone.home
      to: "0"
  action:
    - service: alarm_control_panel.alarm_arm_away
      target:
        entity_id: alarm_control_panel.my_alarm_panel
      data:
        code: "1234"
```

### Send a custom Control4 command

```yaml
action:
  - service: control4.send_command
    data:
      entity_id: light.living_room_dimmer
      command: SET_LEVEL
      params:
        LEVEL: 50
        TIME: 2
```

## Data updates

This integration is mostly push-based over the local network. State changes are delivered in real time via a WebSocket connection to the Control4 Director. The only exception is the media player platform, where playback position is polled every 5 seconds.

During setup or reload of a config entry the integration must contact the Control4 cloud to obtain a short-lived local token. See [Known Limitations](#known-limitations) for more details.

## Known Limitations

- During setup or reload of a config entry the integration must contact the Control4 cloud to obtain a local token. The token has an expiry date and is refreshed automatically in the background.
- If token refresh fails you may see errors when controlling devices or find entity states are stale. Reloading the config entry forces an immediate refresh.
- This integration is reverse-engineered and may not support everything the Control4 app supports.
- Cameras are not (and will not be) supported. If you have Luma cameras, use the [Hikvision integration](https://www.home-assistant.io/integrations/hikvision/). If you have a Control4 DS2 Door Station (Mini), use the [2N Intercom custom integration](https://github.com/mastalir1980/ha-2N-intercom) and the [Control4 Jailbreak tool](https://github.com/garrynewman/Control4.Jailbreak) to retrieve the door station password.


## Actions

### `control4.send_command`

Sends an arbitrary command to any Control4 item by its director item ID or by targeting a Home Assistant entity. Useful for accessing device capabilities not exposed as entity controls.

| Field | Required | Description |
| ----- | -------- | ----------- |
| `entity_id` | No* | One or more Control4 entity IDs to target |
| `item_id` | No* | One or more raw Control4 director item IDs to target |
| `command` | Yes | Command name (e.g. `"SET_LEVEL"`) |
| `params` | No | Dict of parameters for the command (e.g. `{"LEVEL": 50}`) |

\* One of `entity_id` or `item_id` must be provided.

This action supports a response: when called with `response_variable`, it returns `{"sent_count": N}`.

### `control4.send_alarm_keystrokes`

Sends a sequence of keystrokes to a Control4 security panel entity. Useful for entering codes or navigating panel menus not covered by the standard alarm control panel actions.

| Field | Required | Description |
| ----- | -------- | ----------- |
| `entity_id` | Yes | The alarm control panel entity to target |
| `keystrokes` | Yes | String of keystrokes to send, one character at a time |

## Troubleshooting

**Entities are unavailable after a network blip**
The integration reconnects the WebSocket automatically. Entities should return to available within a few seconds of the network recovering. If they stay unavailable, reload the config entry from **Settings** → **Devices & Services** → **Control4** → **⋮** → **Reload**.

**Setup fails with "Cannot connect"**
Verify the controller IP address is reachable from Home Assistant (`ping <ip>` from the HA host). Ensure a static IP or DHCP reservation is set on the router. 4Sight remote access is not supported — the integration only works on the local network.

**Setup fails with "Invalid authentication"**
Use the same email and password you log in to the Control4 app or [customer.control4.com](https://customer.control4.com/) with. These are your Control4 account credentials, not a local controller password.

**Entities are stale or return errors after running for a while**
The local director token has expired and automatic refresh failed. Reload the config entry to force a fresh token.

**SSDP autodiscovery does not find the controller**
Add the integration manually and enter the controller's IP address directly. See [Configuration](#configuration).

**A media player room is missing**
The room must have an audio or video endpoint (receiver, TV, etc.) bound to it in the Control4 project. Rooms with no AV endpoint do not appear as media player entities.

**A device type I expect is not showing up**
Open an issue with the Control4 proxy name of the device (visible in the Control4 Composer software). This integration is reverse-engineered, so some proxy types may not be mapped yet.

## Removing This Integration

Removing this integration is the same as most HACS integrations:

- Go to **Settings** → **Devices & Services** and select the Control4 integration card.
- From the list of devices, select the Control4 entry.
- Next to the entry, select the three-dot menu, then select **Delete**.
- Repeat steps 2 and 3 for every entry you have
- If installed through HACS, go to HACS, select the three-dot menu for this integration, then select **Remove**.
- Then restart Home Assistant to clear the cache.

## Disclaimer

This is **not** the official lawtancool integration or Home Assistant core integration. It is a community vendor fork under the Apache 2.0 license.

This integration is essentially a fuller version of the Control4 integration that is included in Home Assistant by default, and may receive updates faster than the default integration.

This means, however, that this custom integration may not be as stable as the default integration, as the code has not gone through Home Assistant's review process and contains newer features.

This integration is not affiliated with or endorsed by Control4.
