package com.ruoyi.system;

import com.github.pagehelper.PageHelper;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import com.ruoyi.common.security.annotation.EnableCustomConfig;
import com.ruoyi.common.security.annotation.EnableRyFeignClients;
import org.springframework.context.annotation.Bean;

import java.util.Properties;

/**
 * 系统模块
 * 
 * @author ruoyi
 */
@EnableCustomConfig
@EnableRyFeignClients
@SpringBootApplication
public class RuoYiSystemApplication
{

//    @Bean
//    public PageHelper pageHelper() {
//        PageHelper helper = new PageHelper();
//        Properties p = new Properties();
//        p.setProperty("autoRuntimeDialect", "true");
//        // 关键：禁用 SQLParser
//        //p.setProperty("parserDialect", "null");
//        helper.setProperties(p);
//        return helper;
//    }

    public static void main(String[] args)
    {

        SpringApplication.run(RuoYiSystemApplication.class, args);
        System.out.println("(♥◠‿◠)ﾉﾞ  系统模块启动成功   ლ(´ڡ`ლ)ﾞ  \n" +
                " .-------.       ____     __        \n" +
                " |  _ _   \\      \\   \\   /  /    \n" +
                " | ( ' )  |       \\  _. /  '       \n" +
                " |(_ o _) /        _( )_ .'         \n" +
                " | (_,_).' __  ___(_ o _)'          \n" +
                " |  |\\ \\  |  ||   |(_,_)'         \n" +
                " |  | \\ `'   /|   `-'  /           \n" +
                " |  |  \\    /  \\      /           \n" +
                " ''-'   `'-'    `-..-'              ");
    }
}
