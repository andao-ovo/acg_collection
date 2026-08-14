import redis

# 加 protocol=2，让客户端不用 HELLO 命令
r = redis.Redis(host="localhost", port=6379, db=0, protocol=2)

r.set("test", "hello")
print(r.get("test").decode())