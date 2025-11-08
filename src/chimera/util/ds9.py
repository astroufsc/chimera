import logging
import os

from astropy.samp import SAMPHubError, SAMPIntegratedClient

from chimera.util.image import Image

log = logging.getLogger(__name__)


class DS9:
    def __init__(self):
        self.ds9 = SAMPIntegratedClient()
        try:
            self.ds9.connect()
        except SAMPHubError as e:
            raise OSError("Could not connect to DS9 SAMP hub") from e

    def display_image(self, image: Image, frame: int = 1):
        if os.path.exists(image.filename):
            self.display_file(image.filename, frame=frame)
        else:
            self.display_url(image.http(), frame=frame)

    def display_file(self, filename: str, frame: int = 1):
        if not os.path.exists(filename):
            raise OSError(f"{filename} doesn't exists")

        self.cmd(f"frame {frame}")
        self.cmd(f"fits '{filename}'")

    def display_url(self, url: str, frame: int = 1):
        self.cmd(f"frame {frame}")
        self.cmd(f"fits '{url}'")

    def cmd(self, cmd: str) -> None:
        self.ds9.ecall_and_wait("c1", "ds9.set", "10", cmd=cmd)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python ds9.py <filename>")
        sys.exit(1)

    ds9 = DS9()
    ds9.open()
    ds9.display_file(filename=sys.argv[1], frame=1)
