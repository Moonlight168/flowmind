package com.ruoyi.flowable.factory;

import lombok.Getter;
import org.flowable.engine.*;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Component;

import jakarta.annotation.Resource;

/**
 * flowable 引擎注入封装
 * @author XuanXuan
 * @date 2021-04-03
 */
@Component
@Getter
public class FlowServiceFactory {

    @Lazy
    @Resource
    protected RepositoryService repositoryService;

    @Lazy
    @Resource
    protected RuntimeService runtimeService;

    @Lazy
    @Resource
    protected IdentityService identityService;

    @Lazy
    @Resource
    protected TaskService taskService;

    @Lazy
    @Resource
    protected FormService formService;

    @Lazy
    @Resource
    protected HistoryService historyService;

    @Lazy
    @Resource
    protected ManagementService managementService;

    @Lazy
    @Qualifier("processEngine")
    @Resource
    protected ProcessEngine processEngine;

}
