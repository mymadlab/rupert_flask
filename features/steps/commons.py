# pylint: disable=missing-module-docstring,missing-function-docstring,not-callable

import json
import time
from pathlib import Path

from behave import given, then, when


def _normalize_text(value: str) -> str:
	return "".join(character.lower() for character in value if character.isalnum())


@given("a configuration file is passed at start up")
def step_given_configuration_file_passed_at_startup(context):
	context.config_file_path = Path(context.app_module.prosumer.config_file)


@when("we open the configuration file")
def step_when_we_open_the_configuration_file(context):
	context.loaded_config = context.app_module.json_load(str(context.config_file_path))


@then("the configuration file should be loaded")
def step_then_configuration_file_should_be_loaded(context):
	assert isinstance(context.loaded_config, dict)
	assert context.loaded_config == context.app_module.prosumer.config


@given("a request for hello")
def step_given_request_for_hello(context):
	context.request_path = "/hello"


@when("we process the request")
def step_when_we_process_the_request(context):
	context.response = context.client.get(context.request_path)
	context.response_text = context.response.get_data(as_text=True)

	# Action flow schedules async work; wait briefly so assertions can observe side effects.
	send_mock = getattr(context, "send_mock", None)
	if send_mock is not None:
		for _ in range(20):
			if send_mock.await_count > 0:
				break
			time.sleep(0.05)


@then('text returned should contain "{expected_text}"')
def step_then_text_returned_should_contain(context, expected_text):
	actual_normalized = _normalize_text(context.response_text)
	expected_normalized = _normalize_text(expected_text)
	assert expected_normalized in actual_normalized


@given("a JSON file needs to be saved")
def step_given_json_file_needs_to_be_saved(context):
	context.saved_json_path = Path(__file__).resolve().parent / "files" / "saved.json"
	context.json_payload = {
		"service": "rupert_flask",
		"status": "ok",
		"checks": ["hello", "json_save"],
	}


@when("we save the JSON file")
def step_when_we_save_the_json_file(context):
	context.app_module.json_save(str(context.saved_json_path), context.json_payload)


@then("the JSON file should be saved")
def step_then_json_file_should_be_saved(context):
	assert context.saved_json_path.exists()
	saved_content = json.loads(context.saved_json_path.read_text(encoding="utf-8"))
	assert saved_content == context.json_payload
	context.saved_json_path.unlink(missing_ok=True)
