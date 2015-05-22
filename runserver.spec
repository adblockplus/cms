# PyInstaller spec, run "pyinstaller runserver.spec" from repository root to build

# Hidden imports are supposed to be analyzed recursively. However, due to
# a bug in PyInstaller imports from inside hidden modules aren't considered.
# https://github.com/pyinstaller/pyinstaller/issues/1086
def AnalysisWithHiddenImportsWorkaround(scripts, **kwargs):
  import os

  filename = os.path.join(WORKPATH, '_hidden_imports.py')
  with open(filename, 'wb') as file:
    for module in kwargs.pop('hiddenimports'):
      print >>file, 'import ' + module

  a = Analysis([filename] + scripts, **kwargs)
  a.scripts -= [('_hidden_imports', None, None)]
  return a

a = AnalysisWithHiddenImportsWorkaround(
  ['cms/bin/test_server.py'],
  pathex=['.'],
  hiddenimports=[
    'markdown.extensions.attr_list',

    # Used by globals/get_browser_versions.py in web.adblockplus.org
    'xml.dom.minidom',
  ],
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
