-- Atomic token bucket script.
--
-- KEYS[1] - Redis key storing the current token count
-- KEYS[2] - Redis key storing the last refill timestamp
-- ARGV[1] - Capacity (maximum number of tokens)
-- ARGV[2] - Refill rate (tokens per second)
-- ARGV[3] - Cost (tokens to consume for this request)
-- ARGV[4] - Current timestamp (float seconds)
-- ARGV[5] - TTL to apply to the Redis keys (seconds)

local capacity = tonumber(ARGV[1]) or 0
local refill_rate = tonumber(ARGV[2]) or 0
local cost = tonumber(ARGV[3]) or 0
local now = tonumber(ARGV[4]) or 0
local ttl = tonumber(ARGV[5]) or 1

if ttl < 1 then
    ttl = 1
end

local tokens = redis.call("GET", KEYS[1])
if tokens then
    tokens = tonumber(tokens)
else
    tokens = capacity
end

local last_update = redis.call("GET", KEYS[2])
if last_update then
    last_update = tonumber(last_update)
else
    last_update = now
end

local elapsed = now - last_update
if elapsed < 0 then
    elapsed = 0
end

local new_tokens = tokens + (elapsed * refill_rate)
if new_tokens > capacity then
    new_tokens = capacity
end

local allowed = 0
local remaining = new_tokens

if new_tokens >= cost then
    allowed = 1
    remaining = new_tokens - cost
end

if remaining < 0 then
    remaining = 0
end

redis.call("SETEX", KEYS[1], ttl, remaining)
redis.call("SETEX", KEYS[2], ttl, now)

local retry_after = 0

if allowed == 0 then
    local tokens_needed = cost - remaining
    if tokens_needed < 0 then
        tokens_needed = 0
    end

    if refill_rate > 0 then
        retry_after = math.ceil(tokens_needed / refill_rate)
    else
        retry_after = 0
    end
end

return {allowed, retry_after, remaining}
