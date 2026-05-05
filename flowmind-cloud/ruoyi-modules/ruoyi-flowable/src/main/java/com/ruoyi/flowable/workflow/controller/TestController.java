package com.ruoyi.flowable.workflow.controller;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.data.redis.RedisProperties;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/test")
public class TestController {

    @Autowired
    private RedisProperties redisProperties;

    @GetMapping("/redis-config")
    public String getRedisConfig() {
        return "实际生效的Redis配置：\n" +
                "host: " + redisProperties.getHost() + "\n" +
                "port: " + redisProperties.getPort() + "\n" +
                "password: " + (redisProperties.getPassword() == null ? "空" : redisProperties.getPassword()) + "\n" +
                "database: " + redisProperties.getDatabase() + "\n" +
                "timeout: " + redisProperties.getTimeout();
    }
}