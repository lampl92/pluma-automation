from .farmclass import Farmclass
from .board import Board
from .usbrelay import USBRelay
from .powerrelay import PowerRelay
from .serialconsole import SerialConsole
from .hostconsole import HostConsole
from .hub import Hub
from .sdmux import SDMux
from .apc import APC

from .console import TimeoutNoRecieve
from .console import TimeoutNoRecieveStop

class Farm(Farmclass):
    def __init__(self, boards):
        self.boards = boards

    def __repr__(self):
        return "Farm: {}".format(self.boards)

    def board_info(self):
        for b in self.boards:
            ud = b.hub.usb
            print("\n =============== Device [{} - {}] =============".format(
                ud.device, b.name))
            ud.show_info()