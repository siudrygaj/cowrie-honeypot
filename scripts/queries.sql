-- Cowrie Honeypot Analysis Queries
-- Run against cowrie-logs/cowrie.db

-- Top 5 credential pairs attempted
SELECT username, password, COUNT(*) as attempts
FROM login_attempts
GROUP BY username, password
ORDER BY attempts DESC LIMIT 5;

-- Top 5 post-login commands
SELECT command, COUNT(*) as count
FROM commands
GROUP BY command
ORDER BY count DESC LIMIT 5;

-- Sessions by hour of day (UTC)
SELECT strftime('%H', start_time) as hour, COUNT(*) as sessions
FROM sessions
GROUP BY hour ORDER BY hour;

-- Sessions by day
SELECT strftime('%Y-%m-%d', start_time) as day, COUNT(*) as sessions
FROM sessions
GROUP BY day ORDER BY day;
