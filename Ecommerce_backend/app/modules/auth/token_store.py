from enum import IntEnum
from uuid import UUID

from redis import Redis


CREATE_SESSION_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    return 0
end
redis.call('HSET', KEYS[1],
    'user_id', ARGV[1],
    'current_jti', ARGV[2],
    'state', 'active')
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[3]))
return 1
"""

ROTATE_SESSION_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 0 then
    return 0
end

if redis.call('HGET', KEYS[1], 'state') ~= 'active' then
    return 0
end

local stored_user_id = redis.call('HGET', KEYS[1], 'user_id')
local current_jti = redis.call('HGET', KEYS[1], 'current_jti')
if stored_user_id ~= ARGV[1] or current_jti ~= ARGV[2] then
    redis.call('HSET', KEYS[1], 'state', 'revoked')
    redis.call('HDEL', KEYS[1], 'current_jti')
    redis.call('EXPIRE', KEYS[1], tonumber(ARGV[4]))
    return -1
end

redis.call('HSET', KEYS[1], 'current_jti', ARGV[3])
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[4]))
return 1
"""

REVOKE_SESSION_SCRIPT = """
if redis.call('EXISTS', KEYS[1]) == 0 then
    return 0
end
redis.call('HSET', KEYS[1], 'state', 'revoked')
redis.call('HDEL', KEYS[1], 'current_jti')
redis.call('EXPIRE', KEYS[1], tonumber(ARGV[1]))
return 1
"""


class RotationResult(IntEnum):
    REPLAYED = -1
    INVALID = 0
    ROTATED = 1


def _session_key(session_id: UUID) -> str:
    return f"auth:refresh-session:{session_id}"


def create_session(
    client: Redis,
    session_id: UUID,
    user_id: UUID,
    refresh_jti: UUID,
    ttl_seconds: int,
) -> bool:
    result = client.eval(
        CREATE_SESSION_SCRIPT,
        1,
        _session_key(session_id),
        str(user_id),
        str(refresh_jti),
        ttl_seconds,
    )
    return int(result) == 1


def rotate_session(
    client: Redis,
    session_id: UUID,
    user_id: UUID,
    presented_jti: UUID,
    replacement_jti: UUID,
    ttl_seconds: int,
) -> RotationResult:
    result = client.eval(
        ROTATE_SESSION_SCRIPT,
        1,
        _session_key(session_id),
        str(user_id),
        str(presented_jti),
        str(replacement_jti),
        ttl_seconds,
    )
    return RotationResult(int(result))


def revoke_session(client: Redis, session_id: UUID, ttl_seconds: int) -> bool:
    result = client.eval(
        REVOKE_SESSION_SCRIPT,
        1,
        _session_key(session_id),
        ttl_seconds,
    )
    return int(result) == 1