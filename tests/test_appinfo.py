import ctypes
import os
import unittest

from plugin import actions, appinfo
from plugin.komorebi import Window
from plugin.matching import match_score

NOTEPAD = os.path.join(os.environ.get("SystemRoot", r"C:\Windows"), "System32", "notepad.exe")


class FileDescriptionTest(unittest.TestCase):

    def test_reads_the_version_resource(self):
        self.assertTrue(appinfo.file_description(NOTEPAD))

    def test_missing_file(self):
        self.assertIsNone(appinfo.file_description(r"C:\does-not-exist.exe"))


class FriendlyNameTest(unittest.TestCase):

    def test_prefers_description(self):
        self.assertEqual(appinfo.friendly_name({"FileDescription": "Google Chrome", "ProductName": "Google Chrome"}),
                         "Google Chrome")

    def test_product_when_description_extends_it(self):
        self.assertEqual(appinfo.friendly_name({"FileDescription": "Windows Terminal Host",
                                                "ProductName": "Windows Terminal"}), "Windows Terminal")

    def test_rejects_generic_values(self):
        self.assertIsNone(appinfo.friendly_name({"FileDescription": "Notepad.exe",
                                                 "ProductName": "Microsoft® Windows® Operating System"}))


class DisplayNameTest(unittest.TestCase):

    def test_falls_back_to_exe_name(self):
        self.assertEqual(appinfo.display_name(0, "Spotify.exe"), "Spotify")

    def test_generic_hosts_use_exe_name(self):
        self.assertEqual(appinfo.display_name(1234, "ApplicationFrameHost.exe"), "ApplicationFrameHost")

    def test_real_window(self):
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        if not hwnd:
            self.skipTest("no taskbar window (headless session)")
        self.assertTrue(appinfo.process_path(hwnd).lower().endswith("explorer.exe"))
        self.assertNotEqual(appinfo.display_name(hwnd, "explorer.exe"), "explorer")


class GoActionsTest(unittest.TestCase):

    def setUp(self):
        windows = [Window("sublime_text.exe", "notes.md", 1, hwnd=1),
                   Window("sublime_text.exe", "todo.md", 1, hwnd=2),
                   Window("WindowsTerminal.exe", "PowerShell", 2, hwnd=3)]
        names = {1: "Sublime Text", 2: "Sublime Text", 3: "Windows Terminal"}
        self.actions = actions.go_actions(windows, namer=lambda hwnd, exe: names[hwnd])

    def test_friendly_titles_one_per_app(self):
        self.assertEqual([a.title for a in self.actions], ["Go to Sublime Text", "Go to Windows Terminal"])

    def test_searchable_by_friendly_and_exe_name(self):
        terminal = self.actions[1]
        self.assertTrue(match_score(["terminal"], terminal.search_text))
        self.assertTrue(match_score(["windowsterminal"], terminal.search_text))
        self.assertEqual(terminal.steps, [["komorebic", "eager-focus", "WindowsTerminal.exe"]])


if __name__ == "__main__":
    unittest.main()
