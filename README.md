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

### Additional configuration required for alarm control panel

If you are using an alarm control panel, you must go to Home Assistant -> Configuration -> Devices and Services -> Integrations and click "Configure" on the Control4 entry.

In the dialog that appears, choose the Control4 alarm arming modes that you want to correspond to each Home Assistant arming mode. For example, a DSC alarm system uses "Stay" as the "Alarm arm home mode name", and "Away" as the "Alarm arm away mode name". If your alarm system does not use one of the mode names, select `(not set)`. Once you click submit on the dialog, Home Assistant will be able to arm your alarm control panel and detect its state.


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
