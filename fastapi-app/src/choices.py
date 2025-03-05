import enum


class Companies(enum.StrEnum):
    AVIASALES = enum.auto()
    SELECTEL = enum.auto()
    X5 = enum.auto()


class Grades(enum.StrEnum):
    JUNIOR = enum.auto()
    MIDDLE = enum.auto()
    SENIOR = enum.auto()
    TEAM_LEAD = enum.auto()
    INTERN = enum.auto()


class Languages(enum.StrEnum):
    C_SHARP = enum.auto()
    JAVA = enum.auto()
    FRONTEND = enum.auto()
    PYTHON = enum.auto()
    GO = enum.auto()
    C_PLUS_PLUS = enum.auto()
    IOS = enum.auto()
    OTHER = enum.auto()
