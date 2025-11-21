package com.ruoyi.flowable;

import com.ruoyi.common.security.annotation.EnableCustomConfig;
import com.ruoyi.common.security.annotation.EnableRyFeignClients;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cache.annotation.EnableCaching;

/**
 * 工作流中心
 * @author bdn
 */
@EnableCustomConfig
@SpringBootApplication
@EnableCaching
@EnableRyFeignClients
public class RuoYiFlowableApplication {
    public static void main(String[] args)
    {
        SpringApplication.run(RuoYiFlowableApplication.class, args);
        System.out.println("(♥◠‿◠)ﾉﾞ  工作流中心启动成功   ლ(´ڡ`ლ)ﾞ ");
    }
}
