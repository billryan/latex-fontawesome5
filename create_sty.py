import os
import json
import tarfile
import re
import shutil
from datetime import datetime
import requests

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# download fontawesome latest tag from GitHub
LATEST_URL = 'https://github.com/FortAwesome/Font-Awesome/releases/latest'
response = requests.get(LATEST_URL, allow_redirects=False)
latest_tag = response.headers['Location'].split('/')[-1]
latest_tag_tgz_url = 'https://github.com/FortAwesome/Font-Awesome/archive/{}.tar.gz'.format(latest_tag)
OUTPUT_TGZ_FILE = 'fontawesome-{}.tar.gz'.format(latest_tag)
current_dir_files = os.listdir(PROJECT_ROOT)
if OUTPUT_TGZ_FILE not in current_dir_files:
    print('download latest tag: {}...'.format(latest_tag))
    file_response = requests.get(latest_tag_tgz_url)
    with open(OUTPUT_TGZ_FILE, 'wb') as f:
        f.write(file_response.content)

whiltelist = re.compile(r'.*/metadata|otfs/.*')
try:
    t = tarfile.open(OUTPUT_TGZ_FILE, 'r:gz')
except IOError as e:
    print(e)
else:
    raw_output = '/tmp/fontawesome'
    print('extract and move to fontawesome folder...')
    t.extractall(raw_output, members=[m for m in t.getmembers() if whiltelist.search(m.name)])
    src_folder = '{}/Font-Awesome-{}'.format(raw_output, latest_tag)
    dest_folder = '{}/fontawesome'.format(PROJECT_ROOT)
    shutil.move(src_folder, dest_folder)

INPUT_FILE = os.path.join(PROJECT_ROOT, "fontawesome", "metadata", "icons.json")
OUTPUT_FILE = 'fontawesome5.sty'
GENERIC_FILE = 'fontawesomesymbols-generic.tex'
XELUATEX_FILE = 'fontawesomesymbols-xeluatex.tex'

today = datetime.now().strftime('%Y/%m/%d')

OUTPUT_HEADER = r'''
% Identify this package.
\NeedsTeXFormat{LaTeX2e}
\ProvidesPackage{fontawesome5}[__date v__tag fontawesome icons]
% Requirements to use.
\usepackage{fontspec}
% Configure a directory location for fonts(default: 'fontawesome/otfs/')
\newcommand*{\fontdir}[1][fontawesome/otfs/]{\def\@fontdir{#1}}
\fontdir
% Define pro option
\DeclareOption{pro}{
  % Define shortcut to load the Font Awesome pro font.
  \newfontfamily\FA[
    Path=\@fontdir,
    UprightFont=*-Regular-400,
    ItalicFont=*-Light-300,
    BoldFont=*-Solid-900,
  ]{Font Awesome 5 Pro}
}
\ProcessOptions\relax
% Define shortcut to load the Font Awesome font for brands.
\newfontfamily{\FAbrands}[Path=\@fontdir]{Font Awesome 5 Brands-Regular-400}
% Define shortcut to load the Font Awesome font.
\@ifundefined{FA}{%
\newfontfamily\FA[
  Path=\@fontdir,
  UprightFont=*-Regular-400,
  BoldFont=*-Solid-900,
]{Font Awesome 5 Free}
}{}
% Generic command displaying an icon by its name.
\newcommand*{\faicon}[1]{{
  \csname faicon@#1\endcsname
}}

% generic icon commands and aliases
\input{fontawesomesymbols-generic.tex}

% icon-specific commands
\input{fontawesomesymbols-xeluatex.tex}

\endinput
'''.replace('__date', today).replace('__tag', latest_tag)

OUTPUT_LINE = '\expandafter\def\csname faicon@%(name)s\endcsname {%(font)s\symbol{"%(symbol)s}} \n'
GENERIC_LINE = '\def\\fa%(faname)s{\\faicon{%(name)s}}\n'

def hyphens2camel(hyphenstr):
    return ''.join([i.capitalize() for i in hyphenstr.split('-')])

def main():
    with open(INPUT_FILE, 'r') as json_data:
        icons = json.load(json_data)
        with open(OUTPUT_FILE, 'w') as w:
            w.write(OUTPUT_HEADER)
        with open(XELUATEX_FILE, 'w') as x, open(GENERIC_FILE, 'w') as g:
            for icon_name in sorted(icons.keys()):
                font = "\FA" if "brands" not in icons[icon_name]["styles"] else "\FAbrands"
                x.write(
                    OUTPUT_LINE % {
                        'name': icon_name, 'symbol': icons[icon_name]["unicode"].upper(), "font": font
                    }
                )
                g.write(
                    GENERIC_LINE % {
                        'name': icon_name, 'faname': hyphens2camel(icon_name)
                    }
                )


if __name__ == "__main__":
    main()
