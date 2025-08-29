from flask_marshmallow import Marshmallow
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

ma = Marshmallow()
limiter = Limiter(
    get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)