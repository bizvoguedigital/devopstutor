import enum


class CareerTrack(str, enum.Enum):
    CLOUD_ENGINEERING = "cloud_engineering"
    DEVOPS_PLATFORM = "devops_platform"
    HYBRID = "hybrid"


class ExperienceLevel(str, enum.Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    EXPERT = "expert"
