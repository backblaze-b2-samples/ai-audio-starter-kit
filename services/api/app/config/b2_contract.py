import json
import re
from pathlib import Path
from typing import Final

CONTRACT_PATH: Final = Path(__file__).with_name("b2_contract.json")
_CONTRACT: Final = json.loads(CONTRACT_PATH.read_text())

STANDARD_B2_ENV_KEYS: Final = tuple(_CONTRACT["standard_env_keys"])
REQUIRED_B2_ENV_NAMES: Final = tuple(_CONTRACT["required_env"])
PRIMARY_B2_KEY_ID_ENV: Final = _CONTRACT["primary_key_id_env"]
LEGACY_B2_KEY_ID_ENV: Final = _CONTRACT["legacy_key_id_env"]
PRIMARY_B2_PUBLIC_URL_ENV: Final = _CONTRACT["primary_public_url_env"]
LEGACY_B2_PUBLIC_URL_ENV: Final = _CONTRACT["legacy_public_url_env"]
B2_KEY_ID_ENV_NAMES: Final = (PRIMARY_B2_KEY_ID_ENV, LEGACY_B2_KEY_ID_ENV)
B2_PLACEHOLDER_VALUES_BY_ENV: Final = dict(_CONTRACT["placeholders"])
B2_PLACEHOLDER_VALUES: Final = frozenset(B2_PLACEHOLDER_VALUES_BY_ENV.values())
B2_REGION_PATTERN: Final = _CONTRACT["region_pattern"]
B2_REGION_RE: Final = re.compile(B2_REGION_PATTERN)
B2_USER_AGENT_EXTRA: Final = _CONTRACT["user_agent_extra"]


def validate_b2_region(region: str) -> str:
    if not region:
        return region
    if not B2_REGION_RE.fullmatch(region):
        raise ValueError(
            "Invalid B2_REGION. Use only the Backblaze region token, "
            "for example us-west-004."
        )
    return region


def b2_endpoint_url_from_region(region: str) -> str:
    if not region:
        return ""
    return f"https://s3.{validate_b2_region(region)}.backblazeb2.com"
