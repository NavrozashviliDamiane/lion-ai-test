spring.redis.host=localhost
spring.redis.port=6379
spring.redis.password=
spring.redis.timeout=60000ms
spring.redis.jedis.pool.max-active=20
spring.redis.jedis.pool.max-idle=10
spring.redis.jedis.pool.min-idle=5
spring.redis.jedis.pool.max-wait=-1ms


spring.datasource.url=jdbc:mariadb://185.49.165.116:3310/vps_liontest_db?useUnicode=true&characterEncoding=UTF-8&connectionCollation=utf8mb4_unicode_ci
spring.datasource.username=liontest_user
spring.datasource.password=nR2aJ6eS2u
spring.datasource.driver-class-name=org.mariadb.jdbc.Driver

spring.ai.openai.api-key=${OPENAI_API_KEY:}
spring.ai.openai.chat.options.model=gpt-4o
spring.ai.openai.chat.options.temperature=0.3
spring.ai.openai.embedding.options.model=text-embedding-3-small