#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

import os
import re
from typing import Dict, Set, Optional, Tuple, Iterator, Union, List

SLUG = re.compile(r'[- a-zA-Z0-9.]+')
SPDX = re.compile(rf'SPDX-License-Identifier:\s+({SLUG.pattern})')

class Language:
    def __init__(self, *comments: Union[str, Tuple[str, str]], shebang: bool = False) -> None:
        assert(isinstance(shebang, bool))
        self.__shebang = shebang

        self.__match: List[re.Pattern[str]] = []
        for comment in comments:
            init: str
            fini: str = ''
            if isinstance(comment, tuple):
                init, fini = comment
            else:
                init = comment

            pattern = f"^{init}\\s*{SPDX.pattern}\\s*{fini}\\s*$"
            self.__match.append(re.compile(pattern))

    def license(self, path: str) -> Optional[str]:
        "Find the license from the SPDX header."
        with open(path) as f:
            lines = f.readlines()
            for line in lines:
                for matcher in self.__match:
                    match = matcher.match(line)
                    if match:
                        return match.group(1)

        return None

class Index:
    INTERPRETERS: Dict[str, str] = {
        'python3': 'python',
        'python2': 'python',
        'python': 'python',
        'ruby': 'ruby',
        'tsm': 'typescript',
        'sh': 'sh',
    }

    EXTENSIONS: Dict[str, str] = {
        '.py': 'python',
        '.proto': 'protobuf',
        '.rs': 'rust',
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.json': 'json',
        '.toml': 'toml',
        '.md': 'md',
        '.rb': 'ruby',
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'c++',
        '.hpp': 'c++',
        '.cc': 'c++',
        '.hh': 'c++',
        '.cu': 'cuda-c',
        '.cuh': 'cuda-c',
        '.td': 'tablegen',
        '.ts': 'typescript',
        '.sh': 'shell',
    }

    def __init__(self, ignore_paths: Set[str] = set()) -> None:
        self.__ignore_paths = {"./.git"}.union(ignore_paths)
        self.__languages: Dict[str, Language] = {
            'python': Language('#+', shebang=True),
            'ruby': Language('#+', shebang=True),
            'yaml': Language('#+'),
            'c': Language('//+', ('/\\*', '\\*/')),
            'c++': Language('//+', ('/\\*', '\\*/')),
            'cuda-c': Language('//+', ('/\\*', '\\*/')),
            'rust': Language('//+', '//!', ('/\\*', '\\*/')),
            'protobuf': Language('//+', '//!', ('/\\*', '\\*/')),
            'tablegen': Language('//+'),
            'typescript': Language('//+', ('/\\*', '\\*/'), shebang=True),
            'shell': Language('#+', shebang=True),
        }

    def language(self, path: str) -> Optional[Language]:
        name = self.EXTENSIONS.get(os.path.splitext(path)[1])
        if name is None:
            interpreter: Optional[str] = None
            with open(path, "rb") as f:
                if f.read(2) == bytearray('#!'.encode('ascii')):
                    # assume a text file and retry as text file
                    try:
                        with open(path, "r") as t:
                            interpreter = t.readline().rstrip().rsplit(os.path.sep)[-1]
                    except:
                        pass
            name = self.INTERPRETERS.get(interpreter) if interpreter else None
        return self.__languages.get(name) if name else None

    def scan(self, root: str) -> Iterator[Tuple[str, Optional[str], str]]:
        for root_path, dirs, files in os.walk(root):
            # Ignore the specified directories.
            for dir_path in self.__ignore_paths.intersection({os.path.join(root_path, d) for d in dirs}):
                dirs.remove(os.path.basename(dir_path))

            for file in files:
                path = os.path.join(root_path, file)

                # If the file is in the ignore list, skip it.
                if path in self.__ignore_paths:
                    continue
                # If the file is a symlink, don't bother
                if os.path.islink(path):
                    continue
                # If the file is empty skip.
                if os.path.getsize(path) == 0:
                    continue

                # Find the language of the file.
                language = self.language(path)
                if language is None:
                    # File type not supported
                    yield (path, None, "skipped")
                    continue

                # Parse the SPDX header for the language.
                license_result = language.license(path)
                yield (path, license_result, "checked")

if __name__ == '__main__':
    import sys
    import json

    # Check for debug mode
    debug_env = os.getenv('INPUT_DEBUG')
    debug_mode = debug_env is not None and debug_env.lower() == 'true'

    # Validate the arguments
    licenses_env = os.getenv('INPUT_LICENSES')
    if licenses_env is None:
        licenses = sys.argv[1:]
    else:
        licenses = json.loads(licenses_env)
    for license in licenses:
        if not SLUG.match(license):
            print("Invalid license '%s'!" % license)
            raise SystemExit(1)

    ignore_paths_env = os.getenv('INPUT_IGNORE_PATHS')
    if ignore_paths_env is not None:
        ignore_paths = {"./"+p.strip() for p in ignore_paths_env.split("\n")}
    else:
        ignore_paths = set()

    rv = 0
    index = Index(ignore_paths=ignore_paths)
    for path_and_license in index.scan("."):
        path: str
        file_license: Optional[str]
        status: str
        path, file_license, status = path_and_license

        if status == "skipped":
            if debug_mode:
                print(f"⏩ {path}")
        elif file_license is None or file_license not in licenses:
            license_display = file_license if file_license is not None else "NO LICENSE"
            print(f"❌ {license_display:<16} {path}")
            rv = 1
        else:
            # License check passed
            print(f"✅ {path}")

    raise SystemExit(rv)
