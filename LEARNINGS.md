## Config tuning
MAX_ROWS_RETURNED is domain-specific.
Generic DB = 100 (unknown query patterns)
Cricket = 50 (known query patterns, wider but bounded)
Too low = truncated results = wrong answers
Too high = token waste + slow responses
Right value = maximum a legitimate query needs