# Connected environment, weather and ambience

The central EnvironmentDirector owns time, weather, lighting, fog, precipitation,
road wetness and sky metadata. Six JSON weather profiles cover clear/cloudy/rain/
heavy rain/fog/storm. Storm is a rain/wind/fog profile with future lightning hooks,
not a completed lightning simulation. R toggles rain; T toggles day/night in the demo.
Rain changes sky colors, sun energy, volumetric fog, particles, shared road roughness
and color, ambience targets and a state signal for gameplay/NPC consumers.

Wetness accumulates/dries gradually. Current material response is the shared road;
puddle geometry, splashes, rain occlusion and building water streaks remain hooks.
Particle precipitation follows the listener focus and suppresses inside a sheltered
zone. It does not yet perform roof collision for every building. Physical/procedural,
panorama and custom skies use the existing factory; panorama metadata distinguishes
SDR artwork and declared HDR lighting. Import/license/radiance review is still required.

AmbientDirector runs independent base wind, district hum, weather and sheltered
interior layers, plus seeded intermittent one-shots and a positional machinery source.
Zone bounds select interior/exterior response; volumes crossfade rather than snap.
Weather/time events update audio. Audio waveforms are original synthesized placeholders,
not professional recordings. Five PCM fixtures passed sample-count/RMS/clipping checks.
No sound pack or other copyrighted audio was downloaded. Stream paths are replaceable.

Thirteen headless tests verify valid/invalid weather, connected weather-to-audio events,
wetness/drying, rain activation, interior/exterior targets, time wrapping, night sunlight,
layer count and spatial zone entry/exit. GPU rainy and clear previews are required.
This tests parameter/lifecycle behavior; subjective audio mixing remains prototype-level.

Run `pwsh -NoProfile -File tools/world.ps1 preview -Weather rain` or `-Weather clear`.
The shelter at the central sidewalk is a test zone; a future player controller supplies
listener position. The next checkpoint connects events and zones to actual movement.

## Integrated update (2026-09-07)

The actual player supplies listener position. Both sidewalk shelters have cell-owned
zones; unloaded cells cannot apply an audio zone. Exterior wind/city/rain layers crossfade
through an owned low-pass bus (18 kHz outside to 1.5 kHz sheltered), while the interior
layer bypasses it. The bus is removed on shutdown. One-shots and positional machinery
remain synthesized replacement fixtures. A tested cleanup wait prevents audio resources
from remaining in use on bounded GPU exit.

Rain visibility masks the two test shelter footprints below roof height, preventing
streaks through those roofs. This is a bounded shader mask, not general building rain
collision. Other roofs need registered bounds or a reviewed collision solution. No
puddle simulation, water streak material system or physically calibrated HDR is claimed.
Weather also drives the worker's shelter state; time drives its simple night/day activity.
