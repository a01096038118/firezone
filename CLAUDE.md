# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

FireZone detects illegal parking in fire-lane zones (소방시설 주정차금지구역) from drone/ESP32-CAM video. The repo holds three independently built and run apps, not a single Gradle build:

| Dir | What | Port | Package |
|---|---|---|---|
| `firezonePjt_admin/` | Spring Boot admin app: receives detections from Flask, manages admins/users, admin dashboard | 8090 | `com.office.firezonepjt_admin` |
| `firezonePjt_user/` | Spring Boot user app: user signup/signin, read-only dashboard | 8090 (8091 in `local` profile) | `com.office.firezonepjt` |
| `flask/` | Python AI server: camera monitoring, YOLO vehicle/plate/fire-truck detection, PaddleOCR, violation judgment | 5000 | — |

The root-level `src/` and `build/` are stale leftovers from before the split into two Boot modules. Don't edit them; work in the module directories.

Code comments, log messages, and UI text are in Korean. Match that when adding code.

## Commands

Each Spring module has its own Gradle wrapper (Spring Boot 4.1, Java 17, Lombok). Run commands from inside the module directory:

```bash
cd firezonePjt_admin        # or firezonePjt_user
./gradlew bootRun           # Windows: gradlew.bat bootRun
./gradlew build
./gradlew test
./gradlew test --tests "com.office.firezonepjt_admin.FirezonePjtApplicationTests"
```

The only tests are `contextLoads` tests. They boot the full context, so they need the MySQL DB for the active profile to be reachable.

Flask (Python 3.10). Install order matters because ultralytics pulls in `opencv-python`, which conflicts with the contrib build that PaddleOCR needs:

```bash
cd flask
pip install -r requirements.txt
pip uninstall -y opencv-python
pip install --force-reinstall --no-deps opencv-contrib-python==4.10.0.84
python app.py
```

`flask/test_boot.py` is a throwaway script that posts a sample detection to Boot.

## Profiles and environments

`spring.profiles.active` is set in each module's `application.properties` (currently `dev`):
- `local`: MySQL on localhost. `application-local.properties` is a per-developer file and is git-ignored.
- `dev`: DB VM 192.168.56.101, Flask dev VM .107, admin dev VM .103
- `prod`: DB VM .102, Flask prod VM .108, admin prod VM .104

Both Boot apps share one MySQL schema, `DB_FIREZONE`, with `ddl-auto=update`, so entity changes alter the shared tables. Each app uses its own session cookie (`ADMIN_SESSION` / `USER_SESSION`) so both can run in one browser.

Cross-service addresses are hardcoded in several places. Update all of them together when you change environments:
- `flask/config.py`: `BOOT_URL`, `FLASK_PUBLIC_URL`, camera `source` (all can be overridden by env var)
- `static/js/dashboard/common.js` in both Boot modules: `FLASK_BASE_URL`, `ADMIN_BASE_URL`
- admin `detection.allowed-ips` in `application*.properties`. A profile file overrides the base file.

## Architecture

### Detection data flow
1. Flask `camera/monitoring.py` starts a `CameraMonitor` thread per camera in `config.CAMERAS` when the app starts. `camera/auto_capture.py` takes a photo once the scene goes still after motion.
2. `enforcement/enforcement_service.process_photo` runs the full pipeline, serialized by a global lock: `photo_analyzer` matches the zone (feature-matching against `zones/zones.json` reference photos, or auto-detecting yellow outlines via `ai/zone_finder.py`) and detects vehicles and plates. `ai/parking.detectIllegalParking` then compares the photo with the zone's first sighting. If the same car is still in the same spot after `VIOLATION_STAY_SECONDS`, it is a violation. Photos that can't be judged are logged, not sent.
3. `enforcement/violation_handler` → `boot/sender.py` / `boot/api.py` sends `POST /detections` to the **admin** app, as multipart (`data` JSON + `image`) when `BOOT_IMAGE_UPLOAD=true`, otherwise as JSON. Setting `BOOT_ENABLED=false` logs the payload instead of sending it.
4. Admin `DetectionController` checks the caller's IP against `detection.allowed-ips`. `DetectionService.saveDetection` either updates an existing `detection_log` row (same car/zone within `detection.same-event-seconds`, which returns 200) or inserts a new one (201). Images are saved under `detection.image-dir` (`uploads/detections`) and served at `/uploads/detections/**` (`WebConfig`).
5. Both dashboards poll `/detections/list` on the admin app every 5s (`dashboard.js`, `alarm.js`) and pull the live MJPEG stream and images from Flask (`/api/monitor/<camera_id>`, `/api/images/...`). Flask sends `Access-Control-Allow-Origin: *` for this.

Flask HTTP API: blueprints in `flask/routes/`, all under `/api`. Detection DTO fields use the `dl_` prefix. Timestamps are `yyyy-MM-ddTHH:mm:ss` (`BOOT_DATETIME_FORMAT`).

### Spring module layout
Both modules use the same feature-package style: `<feature>/Controller, Service, Dto` + `<feature>/jpa/Entity, Repository` + `<feature>/security/`. Views are Thymeleaf (`templates/`) with shared fragments in `templates/include/`. The dashboard JS and templates are largely duplicated between the two modules, so a dashboard change usually has to go into both.

The admin module also maps the user tables (`UserMemberEntity`→`user_member`, `AuthorityEntity`→`user_authority`) so admins can approve and manage users. Newly approved users get the `APPR_USER` role.

### Security
- **Admin** (`firezonePjt_admin/.../config/SecurityConfig.java`): role hierarchy is CONTROL / MODIFY / MASTER (plus ADMIN). MASTER is also granted MODIFY. Matcher order matters (e.g. `DELETE /detections/delete` must come before `/detections/**`). `POST /detections` is permitAll and CSRF-exempt for Flask. `AdminPermissionRefreshFilter` reloads authorities from the DB on every request, so role changes apply immediately and deleted admins are logged out.
- **User** (`firezonePjt_user/.../config/SecurityConfig.java`): CSRF disabled. Dashboard/detections require `APPR_USER` or `USER`. A disabled (not-yet-approved) account fails login with `error=approval_pending`.

Logging uses log4j2 (`resources/logger/log4j2.xml`). `spring-boot-starter-logging` is excluded in `build.gradle`.
