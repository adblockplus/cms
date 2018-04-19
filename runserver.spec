# PyInstaller spec, run "pyinstaller runserver.spec" from repository root to build

a = Analysis(
    ['cms/bin/test_server.py'],
    pathex=['.'],
    hiddenimports=[
        'markdown.extensions.extra',
        'markdown.extensions.smart_strong',
        'markdown.extensions.fenced_code',
        'markdown.extensions.footnotes',
        'markdown.extensions.attr_list',
        'markdown.extensions.def_list',
        'markdown.extensions.tables',
        'markdown.extensions.abbr',

        # Used by globals/get_browser_versions.py in web.adblockplus.org
        'xml.dom.minidom',
    ],
    excludes=[
        'distutils',
        'doctest',
        'werkzeug',

        # Mac-specific
        'Carbon',
        'Finder',
        'StdSuites',
    ],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='runserver',
    debug=False,
    strip=None,
    upx=False,
    console=True,
)
