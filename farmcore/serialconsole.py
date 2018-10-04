import sys
import time
import serial
import pexpect.fdpexpect

from .console import Console


class SerialConsole(Console):
    def __init__(self, port, baud, timeout=10):
        self.port = port
        self.timeout = timeout
        self.baud = baud
        self._ser = None
        self._pex = None
        super().__init__()

    def __repr__(self):
        return "Serial console device: {}".format(self._ser.port)

    @property
    def is_open(self):
        if not self._ser or not self._pex:
            return False
        else:
            return self._ser.isOpen()

    def open(self):
        self.log("Trying to open serial port {}".format(self.port))
        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baud,
            timeout=self.timeout
        )
        self._pex = pexpect.fdpexpect.fdspawn(
            fd=self._ser.fileno(), timeout=self.timeout)

        if not self.is_open:
            raise RuntimeError(
                "Failed to open serial port {} and init pexpect".format(self.port))

        self.log("Init serial {} success".format(self.port))
        return

    def close(self):
        if self.is_open:
            self._ser.flush()
            self._ser.close()
            self._ser = None
            self.log("Closed serial")
        else:
            self.log("Cannot close serial as it is not open")