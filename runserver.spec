# PyInstaller spec, run "pyinstaller runserver.spec" from repository root to build

a = Analysis(
  ['runserver.py'],
  pathex=['.'],
  hiddenimports=[],
  excludes=['sqlite3', 'django', 'ssl', '_ssl', 'OpenSSL', '_hashlib', 'unittest'],
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
