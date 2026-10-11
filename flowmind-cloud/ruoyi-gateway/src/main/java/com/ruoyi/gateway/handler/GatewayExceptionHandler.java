package com.ruoyi.gateway.handler;

import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.cloud.gateway.support.NotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.web.reactive.error.ErrorWebExceptionHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.server.ServerWebExchange;
import com.ruoyi.common.core.domain.R;
import com.ruoyi.common.core.utils.ServletUtils;
import reactor.core.publisher.Mono;

/**
 * 网关统一异常处理
 *
 * @author ruoyi
 */
@Order(-1)
@Configuration
public class GatewayExceptionHandler implements ErrorWebExceptionHandler
{
    private static final Logger log = LoggerFactory.getLogger(GatewayExceptionHandler.class);

    /** 匹配负载均衡器抛出的 "Unable to find instance for {serviceId}" 异常信息。 */
    private static final Pattern NO_INSTANCE_PATTERN = Pattern.compile(
            "Unable to find instance for ([\\w.\\-]+)");

    @Override
    public Mono<Void> handle(ServerWebExchange exchange, Throwable ex)
    {
        ServerHttpResponse response = exchange.getResponse();

        if (exchange.getResponse().isCommitted())
        {
            return Mono.error(ex);
        }

        if (ex instanceof NotFoundException)
        {
            return handleNotFound(exchange, response, (NotFoundException) ex);
        }

        String msg;
        if (ex instanceof ResponseStatusException)
        {
            msg = ex.getMessage();
        }
        else
        {
            msg = "内部服务器错误";
        }

        log.error("[网关异常处理]请求路径:{},异常信息:{}", exchange.getRequest().getPath(), ex.getMessage());

        return ServletUtils.webFluxResponseWriter(response, msg);
    }

    /**
     * 下游服务无可用实例（未注册/全部宕机）时返回 503 与可定位的服务名提示。
     */
    private Mono<Void> handleNotFound(ServerWebExchange exchange, ServerHttpResponse response,
            NotFoundException ex)
    {
        String serviceName = extractServiceName(ex.getMessage());
        if (serviceName == null)
        {
            log.error("[网关异常处理]请求路径:{},异常信息:{}", exchange.getRequest().getPath(), ex.getMessage());
            return ServletUtils.webFluxResponseWriter(response, "服务未找到");
        }

        log.error("[网关异常处理]请求路径:{},下游服务[{}]无可用实例，请检查服务是否启动并注册到注册中心",
                exchange.getRequest().getPath(), serviceName);
        String msg = String.format("服务[%s]暂不可用（没有找到可用实例），请稍后重试或联系管理员", serviceName);
        return ServletUtils.webFluxResponseWriter(response, HttpStatus.SERVICE_UNAVAILABLE, msg, R.FAIL);
    }

    private String extractServiceName(String reason)
    {
        if (reason == null)
        {
            return null;
        }
        Matcher matcher = NO_INSTANCE_PATTERN.matcher(reason);
        return matcher.find() ? matcher.group(1) : null;
    }
}
