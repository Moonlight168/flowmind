package com.ruoyi.gateway.handler;

import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.BodyInserters;
import org.springframework.web.reactive.function.server.HandlerFunction;
import org.springframework.web.reactive.function.server.ServerRequest;
import org.springframework.web.reactive.function.server.ServerResponse;
import com.ruoyi.common.core.exception.CaptchaException;
import com.ruoyi.common.core.web.domain.AjaxResult;
import com.ruoyi.gateway.service.ValidateCodeService;
import reactor.core.publisher.Mono;

/**
 * 验证码获取
 *
 * @author ruoyi
 */
@Component
public class ValidateCodeHandler implements HandlerFunction<ServerResponse>
{
    private static final Logger log = LoggerFactory.getLogger(ValidateCodeHandler.class);

    @Autowired
    private ValidateCodeService validateCodeService;

    @Override
    public Mono<ServerResponse> handle(ServerRequest serverRequest)
    {
        AjaxResult ajax;
        try
        {
            ajax = validateCodeService.createCaptcha();
        }
        catch (CaptchaException e)
        {
            log.warn("验证码创建失败：{}", e.getMessage());
            ajax = AjaxResult.error("验证码创建失败：" + e.getMessage());
        }
        catch (IOException e)
        {
            log.error("验证码 IO 异常：{}", e.getMessage(), e);
            ajax = AjaxResult.error("验证码服务不可用");
        }
        return ServerResponse.status(HttpStatus.OK).body(BodyInserters.fromValue(ajax));
    }
}
