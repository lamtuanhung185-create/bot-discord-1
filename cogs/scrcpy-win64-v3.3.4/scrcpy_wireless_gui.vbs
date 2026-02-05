Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "python scrcpy_wireless_gui.py", 0, False
Set WshShell = Nothing

