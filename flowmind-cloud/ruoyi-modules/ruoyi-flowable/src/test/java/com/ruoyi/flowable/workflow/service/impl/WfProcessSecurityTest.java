package com.ruoyi.flowable.workflow.service.impl;

import com.ruoyi.common.core.exception.ServiceException;
import com.ruoyi.common.security.utils.SecurityUtils;
import com.ruoyi.flowable.workflow.domain.bo.WfTaskBo;
import com.ruoyi.flowable.workflow.service.IWfCopyService;
import com.ruoyi.flowable.workflow.service.ProcessAccessService;
import com.ruoyi.flowable.workflow.mapper.WfCopyMapper;
import org.flowable.engine.HistoryService;
import org.flowable.engine.history.HistoricProcessInstance;
import org.flowable.engine.history.HistoricProcessInstanceQuery;
import org.flowable.task.api.history.HistoricTaskInstance;
import org.flowable.task.api.history.HistoricTaskInstanceQuery;
import com.ruoyi.flowable.utils.TaskUtils;
import com.ruoyi.system.api.RemoteUserService;
import org.flowable.engine.RuntimeService;
import org.flowable.engine.TaskService;
import org.flowable.engine.runtime.ProcessInstance;
import org.flowable.engine.runtime.ProcessInstanceQuery;
import org.flowable.task.api.Task;
import org.flowable.task.api.TaskQuery;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import java.util.List;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertDoesNotThrow;
import static org.mockito.Mockito.*;

/** 流程操作必须限制为获授权的用户。 */
class WfProcessSecurityTest {
    @Test
    void ownFinishedHistoryCanBeDeletedButSuspendedInstanceCannot() {
        var history = mock(HistoryService.class);
        var query = mock(HistoricProcessInstanceQuery.class, RETURNS_SELF);
        var process = mock(HistoricProcessInstance.class);
        when(history.createHistoricProcessInstanceQuery()).thenReturn(query);
        when(query.singleResult()).thenReturn(process);
        when(process.getStartUserId()).thenReturn("42");
        var runtime = mock(RuntimeService.class);
        var running = mock(ProcessInstanceQuery.class, RETURNS_SELF);
        when(runtime.createProcessInstanceQuery()).thenReturn(running);
        when(running.count()).thenReturn(1L);
        var service = new WfProcessServiceImpl(null, null, null, null, null, null);
        ReflectionTestUtils.setField(service, "historyService", history);
        ReflectionTestUtils.setField(service, "runtimeService", runtime);
        ReflectionTestUtils.setField(service, "processAccess",
            new ProcessAccessService(history, mock(TaskService.class), mock(WfCopyMapper.class)));
        try (var user = mockStatic(SecurityUtils.class)) {
            user.when(SecurityUtils::getUserId).thenReturn(42L);
            assertThrows(ServiceException.class, () -> service.deleteProcessByIds(new String[]{"own"}));
            verify(history, never()).bulkDeleteHistoricProcessInstances(any());
            verify(running, never()).active();
            when(running.count()).thenReturn(0L);
            assertDoesNotThrow(() -> service.deleteProcessByIds(new String[]{"own"}));
            verify(history).bulkDeleteHistoricProcessInstances(List.of("own"));
        }
    }

    @Test
    void legacyDetailAlsoRejectsStrangers() {
        var history = mock(HistoryService.class);
        var query = mock(HistoricProcessInstanceQuery.class, RETURNS_SELF);
        var process = mock(HistoricProcessInstance.class);
        when(history.createHistoricProcessInstanceQuery()).thenReturn(query);
        when(query.singleResult()).thenReturn(process);
        when(process.getStartUserId()).thenReturn("99");
        var historyTasks = mock(HistoricTaskInstanceQuery.class, RETURNS_SELF);
        when(history.createHistoricTaskInstanceQuery()).thenReturn(historyTasks);
        var tasks = mock(TaskService.class);
        var current = mock(TaskQuery.class, RETURNS_SELF);
        when(tasks.createTaskQuery()).thenReturn(current);
        when(current.list()).thenReturn(List.of());
        var service = new WfInstanceServiceImpl(null, null);
        ReflectionTestUtils.setField(service, "processAccess",
            new ProcessAccessService(history, tasks, mock(WfCopyMapper.class)));
        try (var user = mockStatic(SecurityUtils.class); var taskUser = mockStatic(TaskUtils.class)) {
            user.when(SecurityUtils::getUserId).thenReturn(42L);
            taskUser.when(TaskUtils::getCandidateGroup).thenReturn(List.of());
            assertThrows(ServiceException.class, () -> service.queryDetailProcess("other", "deployment"));
        }
    }

    @Test
    void cannotRevokeWithTaskFromAnotherInstance() {
        var service = new WfTaskServiceImpl(mock(RemoteUserService.class), mock(IWfCopyService.class));
        var runtime = mock(RuntimeService.class);
        var query = mock(ProcessInstanceQuery.class, RETURNS_SELF);
        when(runtime.createProcessInstanceQuery()).thenReturn(query);
        when(query.singleResult()).thenReturn(mock(ProcessInstance.class));
        var history = mock(HistoryService.class);
        var historyQuery = mock(HistoricTaskInstanceQuery.class, RETURNS_SELF);
        var historicTask = mock(HistoricTaskInstance.class);
        when(history.createHistoricTaskInstanceQuery()).thenReturn(historyQuery);
        when(historyQuery.singleResult()).thenReturn(historicTask);
        when(historicTask.getProcessInstanceId()).thenReturn("own-instance");
        ReflectionTestUtils.setField(service, "runtimeService", runtime);
        ReflectionTestUtils.setField(service, "historyService", history);
        ReflectionTestUtils.setField(service, "processAccess",
            new ProcessAccessService(history, mock(TaskService.class), mock(WfCopyMapper.class)));
        var bo = new WfTaskBo();
        bo.setTaskId("own-task");
        bo.setProcInsId("other-instance");
        try (var user = mockStatic(TaskUtils.class)) {
            user.when(TaskUtils::getUserId).thenReturn("42");
            assertThrows(ServiceException.class, () -> service.revokeProcess(bo));
            verify(historyQuery).processInstanceId("other-instance");
            verify(historyQuery).finished();
            verify(runtime, never()).createChangeActivityStateBuilder();
        }
    }

    @Test
    void unauthorizedBatchDeletionDoesNotDeleteHistory() {
        var history = mock(HistoryService.class);
        var query = mock(HistoricProcessInstanceQuery.class, RETURNS_SELF);
        var process = mock(HistoricProcessInstance.class);
        when(history.createHistoricProcessInstanceQuery()).thenReturn(query);
        when(query.singleResult()).thenReturn(process);
        when(process.getStartUserId()).thenReturn("99");
        var service = new WfProcessServiceImpl(null, null, null, null, null, null);
        ReflectionTestUtils.setField(service, "historyService", history);
        ReflectionTestUtils.setField(service, "processAccess",
            new ProcessAccessService(history, mock(TaskService.class), mock(WfCopyMapper.class)));
        try (var user = mockStatic(SecurityUtils.class)) {
            user.when(SecurityUtils::getUserId).thenReturn(42L);
            assertThrows(ServiceException.class, () -> service.deleteProcessByIds(new String[]{"other"}));
            verify(history, never()).bulkDeleteHistoricProcessInstances(any());
        }
    }

    @Test
    void strangerCannotCancelProcess() {
        var service = new WfTaskServiceImpl(mock(RemoteUserService.class), mock(IWfCopyService.class));
        var runtime = mock(RuntimeService.class);
        var query = mock(ProcessInstanceQuery.class, RETURNS_SELF);
        var process = mock(ProcessInstance.class);
        when(runtime.createProcessInstanceQuery()).thenReturn(query);
        when(query.singleResult()).thenReturn(process);
        when(process.getStartUserId()).thenReturn("other");
        var tasks = mock(TaskService.class);
        var taskQuery = mock(TaskQuery.class, RETURNS_SELF);
        when(tasks.createTaskQuery()).thenReturn(taskQuery);
        when(taskQuery.list()).thenReturn(List.of(mock(Task.class)));
        ReflectionTestUtils.setField(service, "runtimeService", runtime);
        ReflectionTestUtils.setField(service, "taskService", tasks);
        ReflectionTestUtils.setField(service, "processAccess",
            new ProcessAccessService(mock(HistoryService.class), tasks, mock(WfCopyMapper.class)));
        var bo = new WfTaskBo();
        bo.setProcInsId("instance");
        try (var user = mockStatic(SecurityUtils.class)) {
            user.when(SecurityUtils::getUserId).thenReturn(42L);
            assertThrows(ServiceException.class, () -> service.stopProcess(bo));
            verify(runtime, never()).setVariable(anyString(), anyString(), any());
        }
    }
}
