extends "res://scripts/playable_block.gd"
## A complete, bounded repair mission using the existing streamed world and events.
const SAVE_FILE="user://last_light_save.json"
const TITLES=["01 / RESTART THE WEST RELAY","02 / RESTORE THE SERVICE LINK","03 / RETURN TO THE EXTRACTION BEACON","OPERATION COMPLETE"]
const TARGETS=[Vector3(-50,.4,6),Vector3(0,.4,-6.6),Vector3(22,.4,6),Vector3(22,.4,6)]
var mission_stage:=0
var save_slot:=SAVE_FILE
var started:=false
var panel:PanelContainer
var mission_label:Label
var detail_label:Label
var menu_title:Label
var objective_marker:Label3D
var feedback:=""
var feedback_time:=0.0

func _ready()->void:
	super._ready()
	streamer.chunk_loaded.connect(install_mission_hooks)
	if not Array(OS.get_cmdline_user_args()).any(func(arg):return arg.begins_with("--hour=")):director.set_hour(17.5)
	build_interface()
	add_child(load("res://scripts/distant_skyline.gd").new())
	objective_marker=Label3D.new();objective_marker.billboard=BaseMaterial3D.BILLBOARD_ENABLED
	objective_marker.no_depth_test=true;objective_marker.font_size=48;objective_marker.pixel_size=.008
	objective_marker.modulate=Color(.85,1,.75);add_child(objective_marker)
	for arg in OS.get_cmdline_user_args():
		if arg=="--mission-preview" or arg=="--benchmark":started=true;panel.hide()
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	var beacon:=MeshInstance3D.new()
	var mesh:=CylinderMesh.new();mesh.top_radius=1.4;mesh.bottom_radius=1.4;mesh.height=.08
	beacon.mesh=mesh;beacon.position=TARGETS[2]
	var material:=StandardMaterial3D.new();material.albedo_color=Color(.12,.35,.32)
	material.emission_enabled=true;material.emission=Color(.08,.45,.34);material.emission_energy_multiplier=1.5
	beacon.material_override=material;add_child(beacon)

func install_mission_hooks(id:String)->void:
	if id!="west":return
	var chunk:Node3D=streamer.loaded[id]
	var relay=load("res://scripts/studio_terminal.gd").new()
	relay.persistence_id="west_relay";relay.position=Vector3(14,.95,6)
	chunk.add_child(relay);chunk.terminal=relay
	relay.activated.connect(on_terminal)
	var label:Label3D=relay.get_child(2)
	label.text="WEST RELAY\n[E] RESTART"
	if streamer.states.get(id,{}).has("terminal"):relay.restore(streamer.states[id].terminal)

func on_terminal(id:String)->void:
	if not started:return
	if mission_stage==0 and id=="west_relay":
		mission_stage=1;events.publish("relay_restarted",{"id":id})
	elif mission_stage==1 and id=="service_terminal":
		super.on_terminal(id);mission_stage=2
	else:
		if id=="service_terminal" and streamer.loaded.has("center"):streamer.loaded.center.terminal.active=false
		feedback="Restore the west relay before linking the district.";feedback_time=4
		return
	feedback="Checkpoint saved" if save_game()==OK else "Checkpoint could not be saved";feedback_time=4

func complete_extraction()->void:
	if mission_stage!=2:return
	mission_stage=3;events.publish("mission_complete",{"id":"last_light"})
	save_game();panel.show();menu_title.text="GRID RESTORED\nOperation complete"
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE

func save_game(file:String="")->Error:
	var target:=save_slot if file.is_empty() else file
	var data:Dictionary=capture_save_data()
	data["mission_stage"]=mission_stage
	return load("res://scripts/studio_save.gd").save_state(target,data)

func load_game(file:String="")->bool:
	var target:=save_slot if file.is_empty() else file
	var data:Dictionary=load("res://scripts/studio_save.gd").load_state(target)
	var stage:Variant=data.get("mission_stage")
	if not (stage is int or stage is float) or not is_finite(float(stage)) or stage!=int(stage) or stage<0 or stage>3:return false
	if not super.load_game(target):return false
	mission_stage=int(stage);started=true
	panel.visible=mission_stage==3
	if mission_stage==3:menu_title.text="GRID RESTORED\nOperation complete"
	return true

func _process(delta:float)->void:
	super._process(delta)
	if panel==null:return
	hud.hide();feedback_time=maxf(0,feedback_time-delta)
	player.enabled=started and not panel.visible and not benchmarking
	mission_label.text=TITLES[mission_stage]
	objective_marker.visible=started and mission_stage<3
	objective_marker.position=TARGETS[mission_stage]+Vector3(0,2.4,0)
	objective_marker.text=["WEST RELAY","SERVICE LINK","EXTRACTION",""][mission_stage]
	var distance:=player.position.distance_to(TARGETS[mission_stage])
	detail_label.text=(feedback if feedback_time>0 else "%d m to objective"%int(distance))+"\nWASD Move   Mouse Look   E Interact   Esc Menu   F5 Save   F9 Load"
	if started and mission_stage==2 and distance<2.2:complete_extraction()

func _unhandled_key_input(event:InputEvent)->void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode==KEY_ESCAPE:
		panel.visible=not panel.visible
		Input.mouse_mode=Input.MOUSE_MODE_VISIBLE if panel.visible else Input.MOUSE_MODE_CAPTURED
		return
	if started:super._unhandled_key_input(event)

func button(parent:Node,title:String,action:Callable)->Button:
	var item:=Button.new();item.text=title;item.custom_minimum_size=Vector2(340,48)
	item.pressed.connect(action);parent.add_child(item);return item

func build_interface()->void:
	var layer:=CanvasLayer.new();add_child(layer)
	var screen:=Control.new();screen.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);screen.mouse_filter=Control.MOUSE_FILTER_IGNORE;layer.add_child(screen)
	mission_label=Label.new();mission_label.position=Vector2(36,30);mission_label.add_theme_font_size_override("font_size",25);screen.add_child(mission_label)
	detail_label=Label.new();detail_label.position=Vector2(36,66);detail_label.add_theme_font_size_override("font_size",17);screen.add_child(detail_label)
	var crosshair:=Label.new();crosshair.text="·";crosshair.set_anchors_and_offsets_preset(Control.PRESET_CENTER);crosshair.add_theme_font_size_override("font_size",32);screen.add_child(crosshair)
	panel=PanelContainer.new();panel.position=Vector2(36,160);panel.custom_minimum_size=Vector2(410,0);screen.add_child(panel)
	var style:=StyleBoxFlat.new();style.bg_color=Color(.025,.045,.055,.96);style.border_color=Color(.4,.72,.65);style.set_border_width_all(1);style.content_margin_left=24;style.content_margin_right=24;style.content_margin_top=24;style.content_margin_bottom=24;panel.add_theme_stylebox_override("panel",style)
	var column:=VBoxContainer.new();column.add_theme_constant_override("separation",12);panel.add_child(column)
	menu_title=Label.new();menu_title.text="CINDER / LAST LIGHT\nRestore power. Reconnect. Get home.";menu_title.add_theme_font_size_override("font_size",23);column.add_child(menu_title)
	button(column,"Begin / Resume",func():
		if mission_stage==3:get_tree().reload_current_scene();return
		started=true;panel.hide();Input.mouse_mode=Input.MOUSE_MODE_CAPTURED)
	button(column,"Continue saved operation",func():
		if load_game():Input.mouse_mode=Input.MOUSE_MODE_CAPTURED if mission_stage<3 else Input.MOUSE_MODE_VISIBLE
		else:menu_title.text="No valid operation save found")
	var preset:=OptionButton.new()
	for title in ["LOW","MEDIUM","HIGH","ULTRA","CINEMATIC"]:preset.add_item(title)
	preset.select(quality);preset.item_selected.connect(func(index):quality=index;apply_quality());column.add_child(preset)
	var resolution:=OptionButton.new()
	for title in ["1920 × 1080","2560 × 1440","3840 × 2160 (4K)"]:resolution.add_item(title)
	resolution.select(2 if get_window().size.x>=3840 else 1 if get_window().size.x>=2560 else 0)
	resolution.item_selected.connect(func(index):get_window().size=[Vector2i(1920,1080),Vector2i(2560,1440),Vector2i(3840,2160)][index]);column.add_child(resolution)
	button(column,"Fullscreen / Windowed",func():DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if DisplayServer.window_get_mode()==DisplayServer.WINDOW_MODE_FULLSCREEN else DisplayServer.WINDOW_MODE_FULLSCREEN))
	var credit:=Label.new();credit.text="Surface assets: Poly Haven (CC0)\nPowered by Poly Haven • Original Cinder architecture";credit.add_theme_font_size_override("font_size",12);column.add_child(credit)
	button(column,"Quit",func():get_tree().quit())
