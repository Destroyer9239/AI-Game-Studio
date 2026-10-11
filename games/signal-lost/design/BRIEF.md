# Signal Lost - approved working brief

User accepted these recommendations on 2026-10-10. Working title, not trademark clearance.

Single-player Windows space game in Unreal 5.7.1. Third-person chase camera,
accessible arcade flight with inertia. Investigate a distress signal at an abandoned
orbital station, restore its docking beacon and return safely. Target a polished
ten-minute mission before expansion. Grounded original industrial sci-fi: practical
ship silhouettes, dark metal, readable warm navigation lights and cool station light.

Target: 3840x2160 output at 60 FPS on the local RTX 5070 Ti. Upscaling is allowed
and must be disclosed alongside internal resolution. This is a target, not a result.
Measure uncapped average/p95 frame times and GPU/CPU bottlenecks on a fixed route.
No claim of AAA quality from resolution or engine settings alone.

## Milestones
1. Flight: ship pawn, stable chase camera, acceleration/braking, pitch/yaw/roll,
   collision, reset, speed HUD and a bounded course. Placeholder fighter allowed.
2. Mission: distress marker, beacon interaction, return objective, clear completion,
   restart/save behavior and automated state tests.
3. Hero art: one station exterior, one ship, sparse debris, lighting and restrained
   effects/audio. Inspect actual gameplay views and silhouettes before adding detail.
4. Performance and release candidate: quality settings, packaged gameplay tests,
   repeatable 4K-output benchmark, input/settings polish and credits/provenance.

Exclude multiplayer, procedural planets, walkable interiors, combat, large universe
and paid assets from milestone 1. Do not build all milestones in one AI task.

## Human participation
User supplies three optional references (ship, station, lighting), reviews a short
flight session and reports camera comfort, steering feel and sense of speed.
References guide original designs; they are not permission to copy geometry/logos.
AI handles focused implementation and tests. User handles composition/visual selection
where comfortable. Local builds/render time is not itself equivalent to AI token use.
