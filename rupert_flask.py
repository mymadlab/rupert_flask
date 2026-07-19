"""
Description: Rupert API for initiating events via HTTP calls.
"""
import asyncio
import json
import os
from beartype import beartype
from flask import Flask
from markupsafe import escape
from rupert_prosumer import RupertProsumer

# Configure settings
events_dir = os.environ['RUPERT_EVENTS_DIR']
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
		if action["action"]["event_type"] == "state":
			if action["action"]["state_type"] == "cycle":
				state_cycle(action["action"]["navigate"],
					action["action"]["category"],
					action["action"]["file"])
			if action["action"]["state_type"] == "cycle_set":
				state_cycle_set(action["action"]["current"],
					action["action"]["category"],
					action["action"]["file"])
		else:
			await send_event(action['topic'], action['action'])

@beartype
async def send_event(topic: str, event_dict: dict) -> None:
	"""
	Send an event to a specified topic.
	"""
	# If environment variable RUPERT_TESTING is not set send the event
	if not os.getenv('RUPERT_TESTING'):
		await prosumer.send(topic, json.dumps(event_dict).encode('utf-8'))

@beartype
def state_cycle(navigate: str, category: str, file: str) -> None:
	"""
	Cycle through the states of an event.
	"""
	state = json_load(f"{events_dir}/state/{category}/{file}")
	if navigate == ">": # Next
		state["current"] = state["current"] + 1 if state["current"] + 1 < len(state["actions"]) else 0
	elif navigate == "<": # Previous
		state["current"] = (
  		state["current"] - 1
   		if state["current"] - 1 >= 0
   		else len(state["actions"]) - 1
		)
	json_save(f"{events_dir}/state/{category}/{file}", state)
	run_actions(state["actions"][state["current"]]["actions"])

@beartype
def state_cycle_set(new_current: int, category: str, file: str) -> None:
	"""
	Set the current state of an event.
	"""
	state = json_load(f"{events_dir}/state/{category}/{file}")
	state["current"] = new_current
	json_save(f"{events_dir}/state/{category}/{file}", state)

app = Flask(__name__)

@beartype
@app.route("/event/<event_type>/<name>/<event_profile>")
async def event(event_type: str, name: str, event_profile: str) -> str:
	"""
	Run an action profile based on event type and name.
	"""
	profile = json_load(
	f"{events_dir}/{escape(event_type)}/"
	f"{escape(name)}/"
	f"{escape(event_profile)}.json"
	)
	asyncio.get_running_loop().create_task(run_actions(profile['actions']))
	return (
		f"Running action of Type: {escape(event_type)} Name: {escape(name)} "
		f"Profile: {escape(event_profile)}"
	)

@beartype
@app.route("/hello")
def hello() -> str:
	"""
	Hello check to confirm the API is working.
	"""
	return "Hello, world!"
