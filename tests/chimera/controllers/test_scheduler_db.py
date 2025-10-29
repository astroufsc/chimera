if __name__ == "__main__":

    from chimera.controllers.scheduler.model import Expose, Point, Program, Session

    dark = Expose()
    dark.shutter = "CLOSE"
    dark.exptime = 10
    dark.image_type = "dark"
    dark.object_name = "dark"

    flat = Expose()
    flat.shutter = "OPEN"
    flat.filter = "U"
    flat.exptime = 10
    flat.image_type = "flat"
    flat.object_name = "flat"

    calibration = Program(name="Calibration")
    calibration.actions = [dark, flat]

    science = Program(name="Science")
    science.actions.append(Point(target_name="M7"))

    for i in range(10):
        science.actions.append(Expose(filter="U", exptime=i, shutter="OPEN"))

    session = Session()

    session.add(calibration)
    session.add(science)
    session.commit()
