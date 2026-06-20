# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec — produces a single-file executable.
# Build:  pyinstaller OutreachConsole.spec --clean
#
# Output:
#   dist/OutreachConsole        (Linux)
#   dist/OutreachConsole.exe    (Windows)

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('app/templates', 'app/templates'),
        ('app/static',    'app/static'),
    ],
    hiddenimports=[
        # webdriver-manager
        'webdriver_manager',
        'webdriver_manager.chrome',
        'webdriver_manager.core',
        'webdriver_manager.core.download_manager',
        'webdriver_manager.core.driver_cache',
        'webdriver_manager.core.manager',
        'webdriver_manager.core.os_manager',
        # Selenium
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.common.by',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        # pandas Excel support
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.workbook',
        # Flask / Jinja2
        'flask',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.utils',
        # Email
        'yagmail',
        'yagmail.smtp',
        'smtplib',
        'email',
        'email.mime',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.base',
        # Other
        'PIL',
        'PIL.Image',
        'dotenv',
        'pkg_resources',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='OutreachConsole',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,   # Shows a console window — useful so users can see status/errors
    icon=None,      # Set to 'app/static/icon.ico' if you add a Windows icon
)
