
"""
This is a way to save the startup time when running img2py on lots of
files...
"""

from wx.tools import img2py

command_lines = [
    "-a -F -i -n Icon images/icon-256.png images.py",
    "-a -F -i -n Open_Link images/open-link.png images.py",
    "-a -F -i -n Advanced_Config images/advanced-config.png images.py",
    "-a -F -i -n Exit images/exit.png images.py",
    "-a -F -i -n Bug images/bug.png images.py",
    "-a -F -i -n Feature images/feature.png images.py",
    "-a -F -i -n Github images/github.png images.py",
    "-a -F -i -n Forum images/forum.png images.py",
    "-a -F -i -n Config_Folder images/folder.png images.py",
    "-a -F -i -n Update_Check images/update-check.png images.py",
    "-a -F -i -n About images/about.png images.py",
    "-a -F -i -n Patch images/patch.png images.py",
    "-a -F -i -n Patched images/patched.png images.py",
    "-a -F -i -n Lock images/lock-24.png images.py",
    "-a -F -i -n Unlock images/unlock-24.png images.py",
    "-a -F -i -n Guide images/guide-24.png images.py",
    "-a -F -i -n Sos images/sos-24.png images.py",
    "-a -F -i -n Magisk images/magisk-24.png images.py",
    "-a -F -i -n Add images/add-24.png images.py",
    "-a -F -i -n Delete images/delete-24.png images.py",
    "-a -F -i -n Reload images/reload-24.png images.py",
    "-a -F -i -n Flash images/flash-32.png images.py",
    "-a -F -i -n Splash images/splash.png images.py",
    "-a -F -i -n Process_File images/process_file-24.png images.py",
    ]

if __name__ == "__main__":
    for line in command_lines:
        args = line.split()
        img2py.main(args)

