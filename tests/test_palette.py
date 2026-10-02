import json
import unittest
from unittest import mock

from plugin import komorebi, palette
from plugin.palette import KomorebiPalette
from tests.fixtures import CONFIG, STATE


def make_palette(settings=None):
    """A plugin instance that does not read sys.argv (FlowLauncher.__init__ would)."""
    instance = KomorebiPalette.__new__(KomorebiPalette)
    instance.rpc_request = {"method": "query", "parameters": [""], "settings": settings or {}}
    return instance


class QueryTest(unittest.TestCase):

    def setUp(self):
        patches = [
            mock.patch.object(komorebi, "get_state", return_value=STATE),
            mock.patch.object(komorebi, "load_config", return_value=CONFIG),
            mock.patch.object(palette, "_action_keyword", return_value="k"),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.palette = make_palette()

    def titles(self, query):
        results = sorted(self.palette.query(query), key=lambda r: -r["Score"])
        return [r["Title"] for r in results]

    def steps(self, query, title):
        result = next(r for r in self.palette.query(query) if r["Title"] == title)
        return result["JsonRPCAction"]["parameters"][0]["steps"]

    def test_results_are_json_serialisable(self):
        json.dumps(self.palette.query(""))

    def test_empty_query_lists_the_catalogue(self):
        self.assertGreater(len(self.palette.query("")), 25)

    def test_center_finds_promote(self):
        self.assertEqual(self.titles("center")[0], "Promote to main tile")
        self.assertEqual(self.steps("center", "Promote to main tile"), [["komorebic", "promote-swap"]])

    def test_typo(self):
        self.assertEqual(self.titles("tilling")[0], "Toggle tiling")

    def test_send_lists_existing_workspaces(self):
        self.assertEqual(self.titles("send"), [f"Send to workspace {n}" for n in (1, 2, 3)])
        self.assertEqual(self.steps("send 2", "Send to workspace 2"), [["komorebic", "send-to-workspace", "1"]])

    def test_go_filters_apps(self):
        self.assertEqual(self.titles("go spot"), ["Go to Spotify"])

    def test_apps_in_general_search(self):
        self.assertIn("Go to Spotify", self.titles("spotify"))

    def test_apps_hidden_when_setting_off(self):
        self.palette = make_palette({"show_apps_in_search": False})
        self.assertNotIn("Go to Spotify", self.titles("spotify"))

    def test_rename_keeps_original_case(self):
        self.assertEqual(self.titles("rename Video games"), ["Rename workspace 2 to “Video games”"])

    def test_layout_from_config(self):
        self.assertEqual(self.steps("from config", "Layout: from config"), [
            ["komorebic", "clear-workspace-layout-rules", "0", "1"],
            ["komorebic", "workspace-layout-rule", "0", "1", "3", "ultrawide-vertical-stack"],
            ["komorebic", "change-layout", "bsp"],
            ["komorebic", "retile"],
        ])

    def test_reset_gaps_uses_config(self):
        self.assertEqual(self.steps("reset gaps", "Reset gaps"), [
            ["komorebic", "focused-workspace-padding", "5"],
            ["komorebic", "focused-workspace-container-padding", "8"],
        ])

    def test_restart_follows_settings(self):
        self.palette = make_palette({"start_whkd": False, "start_bar": True})
        self.assertEqual(self.steps("restart", "Restart komorebi"),
                         [["komorebic", "stop", "--bar"], ["sleep", 1], ["komorebic", "start", "--bar"]])

    def test_hint_rewrites_query(self):
        result = next(r for r in self.palette.query("") if r["Title"] == "Send to workspace…")
        self.assertEqual(result["JsonRPCAction"]["parameters"], ["k send ", True])

    def test_context_menu(self):
        result = next(r for r in self.palette.query("tiling") if r["Title"] == "Toggle tiling")
        self.assertEqual(result["ContextData"], ["komorebic toggle-tiling", "toggle-tiling"])
        titles = [item["Title"] for item in self.palette.context_menu(result["ContextData"])]
        self.assertEqual(titles, ["Copy command", "Open komorebic documentation",
                                  "Report an issue or suggest a feature"])


class NotRespondingTest(unittest.TestCase):

    def test_offers_force_restart_first(self):
        with mock.patch.object(komorebi, "get_state", return_value=None), \
                mock.patch.object(palette, "_action_keyword", return_value="k"):
            results = sorted(make_palette().query(""), key=lambda r: -r["Score"])
        self.assertEqual(results[0]["Title"], "komorebi is not responding")

    def test_alert_is_never_filtered_out(self):
        with mock.patch.object(komorebi, "get_state", return_value=None), \
                mock.patch.object(palette, "_action_keyword", return_value="k"):
            titles = [r["Title"] for r in make_palette().query("tiling")]
        self.assertIn("komorebi is not responding", titles)
        self.assertIn("Toggle tiling", titles)


if __name__ == "__main__":
    unittest.main()
