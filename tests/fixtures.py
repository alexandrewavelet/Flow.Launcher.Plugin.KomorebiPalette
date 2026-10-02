"""A small komorebi state and configuration shared by the tests."""

STATE = {
    "monitors": {
        "focused": 0,
        "elements": [{
            "workspaces": {
                "focused": 1,
                "elements": [
                    {"containers": {"elements": [
                        {"windows": {"elements": [{"exe": "chrome.exe", "title": "GitHub"}]}},
                    ]}},
                    {"containers": {"elements": [
                        {"windows": {"elements": [{"exe": "Spotify.exe", "title": "Daft Punk"}]}},
                    ]},
                     "floating_windows": [{"exe": "Everything.exe", "title": "Everything"}]},
                    {"containers": {"elements": []}},
                ],
            },
        }],
    },
}

CONFIG = {
    "default_workspace_padding": 5,
    "default_container_padding": 5,
    "monitors": [{
        "workspaces": [
            {"name": "1", "layout": "BSP"},
            {"name": "2", "layout": "BSP", "layout_rules": {"3": "UltrawideVerticalStack"},
             "container_padding": 8},
            {"name": "3", "layout": "Columns"},
        ],
    }],
}
