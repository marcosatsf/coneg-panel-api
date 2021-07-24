from pydantic import BaseModel

class UpdateLocation(BaseModel):
    """
    Model to exchange info about the location of ConEg system.
    It is used to receive the packet to update the current
    configuration.
    """
    city: str
    state: str