# Cloudinary Uploader for Home Assistant

A Home Assistant custom integration that uploads local images to [Cloudinary](https://cloudinary.com) using signed uploads.

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant UI.
2. Go to **Integrations** → three-dot menu → **Custom repositories**.
3. Add this repository URL and select category **Integration**.
4. Search for "Cloudinary Uploader" and install it.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/cloudinary_uploader` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** → **Devices & Services** → **Add Integration**.
2. Search for **Cloudinary Uploader**.
3. Enter your Cloudinary credentials:
   - **Cloud Name** — found on your Cloudinary dashboard
   - **API Key**
   - **API Secret**
4. The integration validates your credentials before saving.

### Allow external directories

The service enforces Home Assistant's `allowlist_external_dirs`. Add the directories you want to upload from in `configuration.yaml`:

```yaml
homeassistant:
  allowlist_external_dirs:
    - /config/www
    - /tmp
```

## Usage

The integration registers a service: `cloudinary_uploader.upload_image`.

| Field       | Required | Description |
|-------------|----------|-------------|
| `file_path` | Yes      | Absolute path to a local image file. |
| `public_id` | Yes      | Cloudinary public ID. Re-using the same ID overwrites the previous asset. |

### Service call example

```yaml
service: cloudinary_uploader.upload_image
data:
  file_path: /config/www/camera/front_door.jpg
  public_id: home_camera/front_door
```

### Automation example

```yaml
automation:
  - alias: Upload camera snapshot on motion
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_motion
        to: "on"
    action:
      - service: camera.snapshot
        data:
          entity_id: camera.front_door
          filename: /config/www/camera/front_door.jpg
      - service: cloudinary_uploader.upload_image
        data:
          file_path: /config/www/camera/front_door.jpg
          public_id: home_camera/front_door
```

## Development

### Prerequisites

- Python 3.12+
- pip

### Running tests locally

```bash
pip install -r requirements_test.txt
pytest tests/ -v
```

Tests are fully mocked and do not require a running Home Assistant instance or Cloudinary account.

### Manual smoke test (real upload)

A script is provided to verify a real upload against your Cloudinary account:

```bash
export CLOUDINARY_CLOUD_NAME=your_cloud_name
export CLOUDINARY_API_KEY=your_api_key
export CLOUDINARY_API_SECRET=your_api_secret

python scripts/manual_upload_test.py                    # uploads a generated 1x1 PNG
python scripts/manual_upload_test.py path/to/image.jpg  # uploads a specific file
```

The script cleans up the test asset after a successful upload.

## License

MIT
