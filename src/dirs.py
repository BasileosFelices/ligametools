import os

import platformdirs

app_name = "ligametools"

ligametools_user_dirs = platformdirs.PlatformDirs(app_name)

HTML_OUTPUT_DIR = os.path.join(
    ligametools_user_dirs.user_cache_dir, "last_game_scraped/"
)
