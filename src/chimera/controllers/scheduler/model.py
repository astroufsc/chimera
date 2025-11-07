import datetime as dt

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    PickleType,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import backref, relation, sessionmaker

from chimera.core.constants import DEFAULT_PROGRAM_DATABASE

engine = create_engine(f"sqlite:///{DEFAULT_PROGRAM_DATABASE}", echo=False)
metadata = MetaData()
metadata.bind = engine

Session = sessionmaker(bind=engine)
Base = declarative_base(metadata=metadata)


class Targets(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True)
    name = Column(String, default="Program")
    type = Column(String, default=None)
    last_observation = Column(DateTime, default=None)
    observed = Column(Boolean, default=False)
    scheduled = Column(Boolean, default=False)
    target_ra = Column(Float, default=0.0)
    target_dec = Column(Float, default=0.0)
    target_epoch = Column(Float, default=2000.0)
    target_mag = Column(Float, default=0.0)
    mag_filter = Column(String, default=None)

    def __str__(self):
        if self.observed:
            return f"#{self.id} {self.name} [type: {self.type}] #LastObserved@: {self.last_observation}"
        else:
            return f"#{self.id} {self.name} [type: {self.type}] #NeverObserved"


class Program(Base):
    __tablename__ = "program"

    id = Column(Integer, primary_key=True)
    tid = Column(Integer, ForeignKey("targets.id"))
    name = Column(String, ForeignKey("targets.name"))
    pi = Column(String, default="Anonymous Investigator")

    priority = Column(Integer, default=0)

    created_at = Column(DateTime, default=dt.datetime.today())
    finished = Column(Boolean, default=False)
    start_at = Column(Float, default=0.0)
    valid_for = Column(Float, default=-1)

    actions = relation(
        "Action",
        backref=backref("program", order_by="Action.id"),
        cascade="all, delete, delete-orphan",
    )

    def __str__(self):
        return f"#{self.id} {self.name} pi:{self.pi} #actions: {len(self.actions)}"


class Action(Base):
    id = Column(Integer, primary_key=True)
    program_id = Column(Integer, ForeignKey("program.id"))
    action_type = Column("type", String(100))

    __tablename__ = "action"
    __mapper_args__ = {"polymorphic_on": action_type}


class AutoFocus(Action):
    __tablename__ = "action_focus"
    __mapper_args__ = {"polymorphic_identity": "AutoFocus"}

    id = Column(Integer, ForeignKey("action.id"), primary_key=True)
    start = Column(Integer, default=0)
    end = Column(Integer, default=1)
    step = Column(Integer, default=1)
    filter = Column(String, default=None)
    exptime = Column(Float, default=1.0)
    binning = Column(String, default=None)
    window = Column(String, default=None)

    def __str__(self):
        return f"autofocus: start={self.start} end={self.end} step={self.step} exptime={self.exptime}"


class AutoFlat(Action):
    __tablename__ = "action_flat"
    __mapper_args__ = {"polymorphic_identity": "AutoFlats"}

    id = Column(Integer, ForeignKey("action.id"), primary_key=True)
    filter = Column(String, default=None)
    frames = Column(Integer, default=1)
    binning = Column(String, default=None)

    def __str__(self):
        return f"Flat fields: filter={self.filter} frames={self.frames}"


class PointVerify(Action):
    __tablename__ = "action_pv"
    __mapper_args__ = {"polymorphic_identity": "PointVerify"}

    id = Column(Integer, ForeignKey("action.id"), primary_key=True)
    here = Column(Boolean, default=None)
    choose = Column(Boolean, default=None)

    def __str__(self):
        if self.choose is True:
            return "pointing verification: system defined field"
        elif self.here is True:
            return "pointing verification: current field"


class Point(Action):
    __tablename__ = "action_point"
    __mapper_args__ = {"polymorphic_identity": "Point"}

    id = Column(Integer, ForeignKey("action.id"), primary_key=True)
    target_ra_dec = Column(PickleType, default=None)
    target_alt_az = Column(PickleType, default=None)
    dome_az = Column(
        PickleType, default=None
    )  # dome azimuth (can be any azimuth when taking flats)
    dome_tracking = Column(
        PickleType, default=None
    )  # set dome tracking ON/OFF. Default: leave as is.
    offset_ns = Column(PickleType, default=None)  # offset North (>0)/South (<0)
    offset_ew = Column(PickleType, default=None)  # offset West (>0)/East (<0)
    target_name = Column(String, default=None)
    pa = Column(Float, default=None)  # rotator position angle

    def __str__(self):
        offset_ns_str = (
            ""
            if self.offset_ns is None
            else (
                f" north {self.offset_ns}"
                if self.offset_ns > 0
                else f" south {self.offset_ns}"
            )
        )
        offset_ew_str = (
            ""
            if self.offset_ew is None
            else (
                f" west {self.offset_ew}"
                if self.offset_ew > 0
                else f" east {self.offset_ns}"
            )
        )

        offset = (
            ""
            if self.offset_ns is None and self.offset_ew is None
            else f"offset: {offset_ns_str}{offset_ew_str}"
        )

        if self.target_ra_dec is not None:
            return f"point: (ra,dec) {self.target_ra_dec}{offset}"
        elif self.target_alt_az is not None:
            return f"point: (alt,az) {self.target_alt_az}{offset}"
        elif self.target_name is not None:
            return f"point: (object) {self.target_name}{offset}"
        elif self.offset_ns is not None or self.offset_ew is not None:
            return offset
        else:
            return "No target to point to."


class Expose(Action):
    __tablename__ = "action_expose"
    __mapper_args__ = {"polymorphic_identity": "Expose"}

    id = Column(Integer, ForeignKey("action.id"), primary_key=True)
    filter = Column(String, default=None)
    frames = Column(Integer, default=1)

    exptime = Column(Integer, default=5)

    binning = Column(String, default=None)
    window = Column(String, default=None)

    shutter = Column(String, default="OPEN")

    wait_dome = Column(Boolean, default=True)

    image_type = Column(String, default="")
    filename = Column(String, default="$DATE-$TIME")
    object_name = Column(String, default="")

    compress_format = Column(String, default="NO")

    def __str__(self):
        return f"expose: exptime={self.exptime} frames={self.frames} type={self.image_type}"


metadata.create_all(engine)
