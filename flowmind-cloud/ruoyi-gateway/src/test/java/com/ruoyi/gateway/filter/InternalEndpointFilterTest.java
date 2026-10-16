package com.ruoyi.gateway.filter;

import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.ValueSource;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.http.HttpStatus;
import org.springframework.mock.http.server.reactive.MockServerHttpRequest;
import org.springframework.mock.web.server.MockServerWebExchange;
import reactor.core.publisher.Mono;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

/** 内网端点不能通过显式路由或自动发现路由被转发。 */
class InternalEndpointFilterTest {
    @ParameterizedTest
    @ValueSource(strings = {"/webhooks/experiment", "/flowmind-ai/webhooks/experiment",
        "/flowmind-ai-flow/webhooks/experiment", "/webhooks", "/webhooks;x/experiment"})
    void blocksInternalPaths(String path) {
        var exchange = MockServerWebExchange.from(MockServerHttpRequest.post(path));
        var chain = mock(GatewayFilterChain.class);
        new InternalEndpointFilter().filter(exchange, chain).block();
        assertEquals(HttpStatus.FORBIDDEN, exchange.getResponse().getStatusCode());
        verifyNoInteractions(chain);
    }

    @ParameterizedTest
    @ValueSource(strings = {"/design/flow", "/chat/stream", "/system/user/list"})
    void preservesBusinessRoutes(String path) {
        var exchange = MockServerWebExchange.from(MockServerHttpRequest.post(path));
        var chain = mock(GatewayFilterChain.class);
        when(chain.filter(exchange)).thenReturn(Mono.empty());
        new InternalEndpointFilter().filter(exchange, chain).block();
        verify(chain).filter(exchange);
    }
}
