# pylint: disable=missing-module-docstring,missing-function-docstring

import importlib
import os
import sys
from pathlib import Path


def before_all(context):
	module_name = "rupert_flask.rupert_flask"

	workspace_root = Path(__file__).resolve().parents[2]
	if str(workspace_root) not in sys.path:
		sys.path.insert(0, str(workspace_root))

	files_dir = Path(__file__).resolve().parent / "steps" / "files"
	actions_dir = files_dir / "actions"
	config_path = files_dir / "config.json"

	os.environ["RUPERT_ACTIONS_DIR"] = str(actions_dir)
	os.environ["RUPERT_CONFIG_JSON"] = str(config_path)
	os.environ.pop("RUPERT_TESTING", None)

	if module_name in sys.modules:
		app_module = importlib.reload(sys.modules[module_name])
	else:
		app_module = importlib.import_module(module_name)

	context.app_module = app_module
	context.client = app_module.app.test_client()
