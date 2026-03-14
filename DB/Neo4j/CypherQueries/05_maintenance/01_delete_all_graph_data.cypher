// Destructive operation. Use only in disposable environments.

MATCH (n)
DETACH DELETE n;
