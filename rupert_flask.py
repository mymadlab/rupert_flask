"""Rupert Flask interface for APIs and browser clients."""

import asyncio
import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from beartype import beartype
from flask import Flask, Response
from rupert_prosumer import RupertProsumer


LOGGER = logging.getLogger(__name__)
VALID_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

actions_dir: Path
prosumer: RupertProsumer

def _require_env_var(name: str) -> str:
	"""Return the required environment variable value or raise a clear error."""
	value = os.getenv(name)
	if not value:
		raise RuntimeError(f"Missing required environment variable: {name}")
	return value


def _validated_segment(value: str, field_name: str) -> str:
	"""Validate a URL segment used to build action profile paths."""
	if not VALID_SEGMENT_PATTERN.fullmatch(value):
		raise ValueError(f"Invalid {field_name}: only letters, numbers, '_' and '-' are allowed")
	return value


def _resolve_action_profile_path(action_type: str, name: str) -> Path:
	"""Resolve and validate an action profile path under the configured actions directory."""
	resolved_base = actions_dir.resolve()
	action_type_segment = _validated_segment(action_type, "action_type")
	name_segment = _validated_segment(name, "name")
	profile_path = (resolved_base / action_type_segment / f"{name_segment}.json").resolve()
	if resolved_base not in profile_path.parents:
		raise ValueError("Invalid action profile path")
	return profile_path

@beartype
def json_load(json_file: str) -> dict:
	"""
	Load and return contents of a JSON file.
	"""
	with open(json_file, "r", encoding="utf-8") as contents:
		return json.load(contents)

@beartype
def json_save(json_file: str, contents: dict) -> None:
	"""
	Save contents to a JSON file.
	"""
	with open(json_file, "w", encoding="utf-8") as outfile:
		json.dump(contents, outfile)

@beartype
async def run_actions(actions: list[dict[str, Any]]) -> None:
	"""
	Run a list of actions.
	"""
	for action in actions:
		action_payload = action.get("action", {})
		if action_payload.get("action_type") == "state":
			state_type = action_payload.get("state_type")
			if state_type == "cycle":
				await state_cycle(
					action_payload["navigate"],
					action_payload["category"],
					action_payload["file"],
				)
			elif state_type == "cycle_set":
				state_cycle_set(
					action_payload["current"],
					action_payload["category"],
					action_payload["file"],
				)
		else:
			await send_action(action["topic"], action_payload)

@beartype
async def send_action(topic: str, action_dict: dict) -> None:
	"""
	Send an action to a specified topic.
	"""
	# If environment variable RUPERT_TESTING is not set, send the action.
	if not os.getenv('RUPERT_TESTING'):
		await prosumer.send(topic, json.dumps(action_dict).encode('utf-8'))

@beartype
async def state_cycle(navigate: str, category: str, state_file: str) -> None:
	"""
	Cycle through the states of an action.
	"""
	state = json_load(str(actions_dir / category / "state" / state_file))
	if navigate == ">": # Next
		state["current"] = state["current"] + 1 if state["current"] + 1 < len(state["actions"]) else 0
	elif navigate == "<": # Previous
		state["current"] = (
  		state["current"] - 1
   		if state["current"] - 1 >= 0
   		else len(state["actions"]) - 1
		)
	json_save(str(actions_dir / category / "state" / state_file), state)
	await run_actions(state["actions"][state["current"]]["actions"])

@beartype
def state_cycle_set(new_current: int, category: str, state_file: str) -> None:
	"""
	Set the current state of an action.
	"""
	state = json_load(str(actions_dir / category / "state" / state_file))
	state["current"] = new_current
	json_save(str(actions_dir / category / "state" / state_file), state)


def create_app() -> Flask:
	"""Create and configure the Flask application."""
	global actions_dir
	global prosumer

	actions_dir = Path(_require_env_var("RUPERT_ACTIONS_DIR")).expanduser().resolve()
	config_json = _require_env_var("RUPERT_CONFIG_JSON")
	prosumer = RupertProsumer(config_json)

	app = Flask(__name__)
	return app

app = create_app()

# Media
# Static
@beartype
@app.route("/master")
def master() -> Response:
	"""
	Display media player controls for a specific room
	"""
	html = "<html><head><title>Media Player Controls</title></head><body>"
	html += "<h1>Media Player Controls for Room: Master</h1>"
	html += "<p style=\"font-size: 350%;\"><a href='/api/action/master/sleep'>Play Sleep</a></p>"
	html += "<p style=\"font-size: 350%;\"><a href='/api/action/master/pause'>Pause</a></p>"
	html += "</body></html>"
	return Response(html, mimetype="text/html")

# API's
@beartype
@app.route("/api/action/<action_type>/<name>")
async def api_action(action_type: str, name: str) -> Response:
	"""
	Run an action profile based on action type and name.
	"""
	try:
		profile_path = _resolve_action_profile_path(action_type, name)
		profile = json_load(str(profile_path))
		actions = profile["actions"]
	except ValueError as exc:
		return Response(str(exc), mimetype="text/plain", status=400)
	except FileNotFoundError:
		return Response("Action profile not found", mimetype="text/plain", status=404)
	except (KeyError, json.JSONDecodeError, TypeError) as exc:
		LOGGER.exception("Invalid action profile for type=%s name=%s", action_type, name)
		return Response(f"Invalid action profile: {exc}", mimetype="text/plain", status=500)

	asyncio.get_running_loop().create_task(run_actions(actions))
	return Response(
		f"Running action of Type: {action_type} Name: {name}",
		mimetype="text/plain",
	)

@beartype
@app.route("/hello")
def hello() -> Response:
	"""
	Hello check to confirm the API is working.
	"""
	return Response("Hello, world!", mimetype="text/plain")
