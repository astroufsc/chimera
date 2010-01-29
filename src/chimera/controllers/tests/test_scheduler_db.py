
if __name__ == '__main__':

    from chimera.controllers.scheduler.model import Program, Expose, Point, Session

    dark = Expose()
    dark.shutter = "CLOSE"
    dark.exptime = 10
    dark.imageType = "dark"
    dark.objectName = "dark"

    flat = Expose()
    flat.shutter = "OPEN"
    flat.filter = "U"
    flat.exptime = 10
    flat.imageType = "flat"
    flat.objectName = "flat"
    
    calibration = Program(name="Calibration")
    calibration.actions = [dark, flat]

    science = Program(name="Science")
    science.actions.append(Point(targetName="M7"))
    
    for i in range(10):
        science.actions.append(Expose(filter="U", exptime=i, shutter="OPEN"))

    session = Session()

    session.add(calibration)
    session.add(science)    
    session.commit()    
