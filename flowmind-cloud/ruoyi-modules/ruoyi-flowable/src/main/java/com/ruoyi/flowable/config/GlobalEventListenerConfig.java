package com.ruoyi.flowable.config;

import com.ruoyi.flowable.listener.GlobalEventListener;
import lombok.AllArgsConstructor;
import lombok.RequiredArgsConstructor;
import org.flowable.common.engine.api.delegate.event.FlowableEngineEventType;
import org.flowable.engine.RuntimeService;
import org.flowable.spring.SpringProcessEngineConfiguration;
import org.flowable.spring.boot.EngineConfigurationConfigurer;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Lazy;
import org.springframework.context.event.ContextRefreshedEvent;

/**
 * flowable全局监听配置
 *
 * @author ssc*/


@Configuration
@RequiredArgsConstructor
public class GlobalEventListenerConfig {
	private final GlobalEventListener globalEventListener;

	/**流程引擎初始化之后执行，十分安全*/
	@Bean
	public EngineConfigurationConfigurer<SpringProcessEngineConfiguration> globalListenerConfigurer() {
		return engineConfiguration -> {
			engineConfiguration.setEventListeners(java.util.List.of(globalEventListener));
		};
	}
}


/*
package com.ruoyi.flowable.config;

import com.ruoyi.flowable.listener.GlobalEventListener;
import lombok.AllArgsConstructor;
import org.flowable.common.engine.api.delegate.event.FlowableEngineEventType;
import org.flowable.engine.RuntimeService;
import org.springframework.context.ApplicationListener;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.event.ContextRefreshedEvent;

*/
/**
 * flowable全局监听配置
 *
 * @author ssc
 *//*

@Configuration
@AllArgsConstructor
public class GlobalEventListenerConfig implements ApplicationListener<ContextRefreshedEvent> {

	private final GlobalEventListener globalEventListener;
	private final RuntimeService runtimeService;

	@Override
	public void onApplicationEvent(ContextRefreshedEvent event) {
		// 流程正常结束
		runtimeService.addEventListener(globalEventListener, FlowableEngineEventType.PROCESS_COMPLETED);
	}
}
*/
