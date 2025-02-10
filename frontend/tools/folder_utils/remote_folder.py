import platform
import os
from smb.SMBConnection import SMBConnection



conn = SMBConnection("mythezone","19891016Zmy!","macmini4","sta")
assert conn.connect("10.16.12.105")