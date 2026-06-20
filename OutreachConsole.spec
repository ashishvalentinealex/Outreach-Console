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
        'webdriver_manager.core.http',
        'webdriver_manager.core.file_manager',
        'webdriver_manager.core.logger',
        # Selenium — full tree to avoid missing submodule errors
        'selenium',
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.chrome.webdriver',
        'selenium.webdriver.chrome.service',
        'selenium.webdriver.chrome.options',
        'selenium.webdriver.chromium',
        'selenium.webdriver.chromium.webdriver',
        'selenium.webdriver.chromium.service',
        'selenium.webdriver.chromium.options',
        'selenium.webdriver.remote',
        'selenium.webdriver.remote.webdriver',
        'selenium.webdriver.remote.command',
        'selenium.webdriver.remote.remote_connection',
        'selenium.webdriver.remote.errorhandler',
        'selenium.webdriver.common',
        'selenium.webdriver.common.by',
        'selenium.webdriver.common.keys',
        'selenium.webdriver.common.action_chains',
        'selenium.webdriver.common.actions',
        'selenium.webdriver.common.actions.action_builder',
        'selenium.webdriver.common.actions.wheel_actions',
        'selenium.webdriver.common.actions.pointer_actions',
        'selenium.webdriver.common.actions.key_actions',
        'selenium.webdriver.support',
        'selenium.webdriver.support.ui',
        'selenium.webdriver.support.expected_conditions',
        'selenium.webdriver.support.wait',
        'selenium.common',
        'selenium.common.exceptions',
        # pandas / Excel
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.workbook',
        'openpyxl.reader.excel',
        'openpyxl.writer.excel',
        'pandas',
        'pandas.io.formats.style',
        # Flask / Jinja2 / Werkzeug
        'flask',
        'jinja2',
        'jinja2.ext',
        'jinja2.loaders',
        'werkzeug',
        'werkzeug.utils',
        'werkzeug.serving',
        # Email
        'yagmail',
        'yagmail.smtp',
        'smtplib',
        'email',
        'email.mime',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.base',
        'email.mime.image',
        # Imaging
        'PIL',
        'PIL.Image',
        'PIL.JpegImagePlugin',
        'PIL.PngImagePlugin',
        # Other
        'dotenv',
        'pkg_resources',
        'pkg_resources.py2_warn',
        'certifi',
        'urllib3',
        'requests',
        'charset_normalizer',
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
