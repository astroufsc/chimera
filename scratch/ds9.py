from astropy.samp import SAMPIntegratedClient

ds9 = SAMPIntegratedClient()
ds9.connect()

ds9.ecall_and_wait("c1", "ds9.set", "10", cmd="url http://localhost:9000/pleiades.fits")
ds9.ecall_and_wait("c1", "ds9.set", "10", cmd="scale mode 99.5")
ds9.ecall_and_wait("c1", "ds9.set", "10", cmd="zscale")
ds9.ecall_and_wait("c1", "ds9.set", "10", cmd="zoom to fit")
