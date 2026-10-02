import unittest

from plugin import komorebi
from plugin.settings import Settings
from tests.fixtures import CONFIG, STATE


class StateTest(unittest.TestCase):

    def test_focus(self):
        self.assertEqual(komorebi.get_focus(STATE), komorebi.Focus(monitor=0, workspace=1, workspace_count=3))

    def test_focus_without_state(self):
        self.assertIsNone(komorebi.get_focus(None))

    def test_windows_include_floating(self):
        windows = komorebi.get_windows(STATE)
        self.assertEqual([(w.exe_name, w.workspace) for w in windows],
                         [("chrome", 1), ("Spotify", 2), ("Everything", 2)])


class ConfigTest(unittest.TestCase):

    def test_layout_names_converted_to_cli_syntax(self):
        self.assertEqual(komorebi.to_cli_layout("UltrawideVerticalStack"), "ultrawide-vertical-stack")
        self.assertEqual(komorebi.to_cli_layout("BSP"), "bsp")

    def test_configured_layout_and_rules(self):
        self.assertEqual(komorebi.configured_layout(CONFIG, 0, 1), ("bsp", {3: "ultrawide-vertical-stack"}))
        self.assertEqual(komorebi.configured_layout(CONFIG, 0, 2), ("columns", {}))

    def test_configured_gaps_prefer_workspace_values(self):
        self.assertEqual(komorebi.configured_gaps(CONFIG, 0, 1), (5, 8))
        self.assertEqual(komorebi.configured_gaps({}, 0, 0), (10, 10))


class SettingsTest(unittest.TestCase):

    def test_defaults(self):
        settings = Settings.from_dict(None)
        self.assertTrue(settings.start_whkd)
        self.assertEqual(settings.start_flags, ["--whkd"])

    def test_string_values_from_flow(self):
        settings = Settings.from_dict({"start_whkd": "false", "start_bar": True, "action_delay_ms": "900",
                                       "zen_workspace_padding": "oops"})
        self.assertEqual(settings.start_flags, ["--bar"])
        self.assertEqual(settings.action_delay_ms, 900)
        self.assertEqual(settings.zen_workspace_padding, 80)


if __name__ == "__main__":
    unittest.main()
