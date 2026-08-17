import contextlib
import importlib.util
import io
import pathlib
import unittest
from unittest import mock


SERVER_PATH = pathlib.Path(__file__).parents[1] / "scripts" / "server.py"
SPEC = importlib.util.spec_from_file_location("storage_analyzer_server", SERVER_PATH)
SERVER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SERVER)


class ServerLifecycleTest(unittest.TestCase):
    def test_idle_timeout_closes_server(self):
        output = io.StringIO()
        empty_report = ({}, "", set(), set(), set())

        with mock.patch.object(SERVER, "load", return_value=empty_report), \
                mock.patch.object(SERVER.webbrowser, "open"), \
                contextlib.redirect_stdout(output):
            SERVER.main(["analysis.json", "--idle-timeout", "0.05"])

        self.assertIn("服务已因空闲超时自动停止", output.getvalue())

    def test_negative_idle_timeout_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                SERVER.parse_args(["analysis.json", "--idle-timeout", "-1"])


if __name__ == "__main__":
    unittest.main()
