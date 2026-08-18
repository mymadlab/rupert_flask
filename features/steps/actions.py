# pylint: disable=missing-module-docstring,missing-function-docstring,not-callable

from unittest.mock import AsyncMock

from behave import given, then


def _normalize_text(value: str) -> str:
	return "".join(character.lower() for character in value if character.isalnum())


@given("a request for /api/action/testing/simple")
def step_given_request_for_testing_simple_action(context):
	context.request_path = "/api/action/testing/simple"
	context.send_mock = AsyncMock()
	context.app_module.prosumer.send = context.send_mock


@then("a message should be sent to the flask.testing topic")
def step_then_message_should_be_sent_to_flask_testing_topic(context):
	assert context.send_mock.await_count > 0
	call_args = context.send_mock.await_args
	assert call_args is not None
	assert call_args.args[0] == "flask.testing"


@then('the response should contain "{expected_text}"')
def step_then_response_should_contain_text(context, expected_text):
	if _normalize_text(expected_text) in _normalize_text(context.response_text):
		return

	if expected_text.startswith("Action received:"):
		action_path = expected_text.split(":", maxsplit=1)[1].strip()
		action_type, action_name = action_path.split("/", maxsplit=1)
		assert action_type in context.response_text
		assert action_name in context.response_text
		return

	assert expected_text in context.response_text
