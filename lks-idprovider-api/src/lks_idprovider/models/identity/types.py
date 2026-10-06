from typing import Union

from .client_identity import ClientIdentity
from .user import User

# Type aliases for convenience
IdentityType = Union[User, ClientIdentity]
