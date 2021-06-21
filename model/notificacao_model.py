from pydantic import BaseModel

class UpdateNotifi(BaseModel):
    """
    Model to exchange info about the method and the message.
    It is used to receive the packet to update the current
    configuration.
    """
    method: str
    message: str