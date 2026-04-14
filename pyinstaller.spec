import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['desktop_main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('config/', 'config/'),
        ('resources/styles/', 'resources/styles/'),
        ('data/', 'data/'),
        ('logs/', 'logs/'),
    ],
    hiddenimports=[
        'playwright',
        'playwright._impl._api_types',
        'pyyaml',
        'loguru',
        'beautifulsoup4',
        'lxml',
        'sqlalchemy',
        'asyncio',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AI新闻自动化系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)