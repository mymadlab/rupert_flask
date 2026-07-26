"""
Description: Rupert Flask interface for API's and browser clients.
"""
import asyncio
import json
import os
from beartype import beartype
from flask import Flask
from markupsafe import escape
from rupert_prosumer import RupertProsumer

# Configure settings
actions_dir = os.environ['RUPERT_ACTIONS_DIR']
config_json = os.environ['RUPERT_CONFIG_JSON']

prosumer = RupertProsumer(config_json)

@beartype
def json_load(json_file: str) -> dict:
	"""
	Load and return contents of a JSON file.
	"""
	with open(json_file, 'r', encoding='utf-8') as contents:
		contents_json = contents.read()
	return json.loads(contents_json)

@beartype
def json_save(json_file: str, contents: dict) -> None:
	"""
	Save contents to a JSON file.
	"""
	with open(json_file, encoding="utf-8", mode="w") as outfile:
		json.dump(contents, outfile)

@beartype
async def run_actions(actions: list[dict]) -> None:
	"""
	Run a list of actions.
	"""
	for action in actions:
		if action["action"]["action_type"] == "state":
			if action["action"]["state_type"] == "cycle":
				state_cycle(action["action"]["navigate"],
					action["action"]["category"],
					action["action"]["file"])
			if action["action"]["state_type"] == "cycle_set":
				state_cycle_set(action["action"]["current"],
					action["action"]["category"],
					action["action"]["file"])
		else:
			await send_action(action['topic'], action['action'])

@beartype
async def send_action(topic: str, action_dict: dict) -> None:
	"""
	Send an action to a specified topic.
	"""
	# If environment variable RUPERT_TESTING is not set send the action
	if not os.getenv('RUPERT_TESTING'):
		await prosumer.send(topic, json.dumps(action_dict).encode('utf-8'))

@beartype
def state_cycle(navigate: str, category: str, file: str) -> None:
	"""
	Cycle through the states of an action.
	"""
	state = json_load(f"{actions_dir}/state/{category}/{file}")
	if navigate == ">": # Next
		state["current"] = state["current"] + 1 if state["current"] + 1 < len(state["actions"]) else 0
	elif navigate == "<": # Previous
		state["current"] = (
  		state["current"] - 1
   		if state["current"] - 1 >= 0
   		else len(state["actions"]) - 1
		)
	json_save(f"{actions_dir}/state/{category}/{file}", state)
	run_actions(state["actions"][state["current"]]["actions"])

@beartype
def state_cycle_set(new_current: int, category: str, file: str) -> None:
	"""
	Set the current state of an action.
	"""
	state = json_load(f"{actions_dir}/state/{category}/{file}")
	state["current"] = new_current
	json_save(f"{actions_dir}/state/{category}/{file}", state)

app = Flask(__name__)

# Media
# API's
@beartype
@app.route("/Master")
def api_action() -> str:
	"""
	Display media player controls for a specific room
	"""
	HTML = "<html><head><title>Media Player Controls</title></head><body>"
	HTML += f"<h1>Media Player Controls for Room: Master</h1>"
	HTML += f"<p><a href='/api/action/master/sleep'>Play Sleep</a></p>"
	HTML += f"<p><a href='/api/action/master/pause'>Pause</a></p>"
	HTML += "</body></html>"
	return HTML


# API's
@beartype
@app.route("/api/action/<action_type>/<name>")
async def api_action(action_type: str, name: str) -> str:
	"""
	Run an action profile based on action type and name.
	"""
	profile = json_load(
	f"{actions_dir}/{escape(action_type)}/"
	f"{escape(name)}.json"
	)
	asyncio.get_running_loop().create_task(run_actions(profile['actions']))
	return (
		f"Running action of Type: {escape(action_type)} Name: {escape(name)} "
	)

@beartype
@app.route("/hello")
def hello() -> str:
	"""
	Hello check to confirm the API is working.
	"""
	return "Hello, world!"
