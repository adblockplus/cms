# PyInstaller spec, run "pyinstaller runserver.spec" from repository root to build

a = Analysis(
  ['runserver.py'],
  pathex=['.'],
  hiddenimports=[],
  excludes=[
    'distutils',
    'doctest',
    'ssl',
    '_ssl',
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
  console=True
)
