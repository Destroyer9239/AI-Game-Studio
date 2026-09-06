# Video source media

The existing Higgsfield adapter implements the reviewed `generate_video` route.
It is registered once; this directory is the extension location for future video
backends, not a duplicate integration. Requests use the same paid plan/approval
contract. Downloaded clips are staged as source media with provenance and never
automatically added to the Godot runtime. `local_video` remains non-executable
until a local backend is installed, reviewed and tested.
