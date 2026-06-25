"""Constants for the ESO Free Capacity Check integration."""

DOMAIN = "eso_check"

CONF_OBJECT_NUMBER = "object_number"
CONF_CHECK_URL = "check_url"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_CHECK_URL = (
    "https://www.eso.lt/namams/gaminantis-vartotojas/laisvos-galios-pasitikrinimas/362"
)
DEFAULT_SCAN_INTERVAL = 86400  # 24 hours

NO_CAPACITY_PHRASE = "Laisvos galios pastotėje nėra"

XSRF_COOKIE_PREFIX = "SITEXSRF"
XSRF_HEADER_PREFIX = "X-"

STATE_AVAILABLE = "true"
STATE_NONE = "none"
