package com.ruoyi.flowable.workflow.service.impl;

import com.ruoyi.common.core.exception.ServiceException;
import com.ruoyi.flowable.common.constant.ProcessConstants;
import com.ruoyi.flowable.utils.TaskUtils;
import com.ruoyi.flowable.workflow.domain.bo.WfTaskBo;
import com.ruoyi.flowable.workflow.service.IWfCopyService;
import com.ruoyi.system.api.RemoteUserService;
import org.flowable.bpmn.model.BpmnModel;
import org.flowable.bpmn.model.MultiInstanceLoopCharacteristics;
import org.flowable.bpmn.model.UserTask;
import org.flowable.engine.RuntimeService;
import org.flowable.engine.TaskService;
import org.flowable.task.api.Task;
import org.flowable.task.api.TaskQuery;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;
import java.util.*;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.*;

/** 下一审批人分配与系统变量、退回查询权限边界。 */
class WfTaskAssignmentTest {
    private final TaskService tasks = mock(TaskService.class);
    private final RuntimeService runtime = mock(RuntimeService.class);
    private final TaskQuery query = mock(TaskQuery.class, RETURNS_SELF);
    private final WfTaskServiceImpl service = new WfTaskServiceImpl(mock(RemoteUserService.class), mock(IWfCopyService.class));

    WfTaskAssignmentTest() {
        ReflectionTestUtils.setField(service, "taskService", tasks);
        ReflectionTestUtils.setField(service, "runtimeService", runtime);
        when(tasks.createTaskQuery()).thenReturn(query);
    }

    private Task task(String id, String key) {
        Task task = mock(Task.class);
        when(task.getId()).thenReturn(id);
        when(task.getTaskDefinitionKey()).thenReturn(key);
        when(task.getExecutionId()).thenReturn("exec-" + id);
        return task;
    }

    private BpmnModel model(boolean sequential) {
        BpmnModel model = new BpmnModel();
        org.flowable.bpmn.model.Process process = new org.flowable.bpmn.model.Process();
        UserTask node = new UserTask();
        node.setId("approve");
        node.setAssignee("${reviewer}");
        MultiInstanceLoopCharacteristics loop = new MultiInstanceLoopCharacteristics();
        loop.setElementVariable("reviewer");
        loop.setSequential(sequential);
        node.setLoopCharacteristics(loop);
        process.addFlowElement(node);
        model.addProcess(process);
        return model;
    }

    private void assign(BpmnModel model, String ids) {
        ReflectionTestUtils.invokeMethod(service, "assignNextUsers", model, "instance", ids, Set.of());
    }

    @Test
    void fewerReviewersReplaceInsteadOfAddingAndDoNotCountAsCompleted() {
        doReturn(List.of(task("a", "approve"), task("b", "approve"))).when(query).list();
        assign(model(false), "99");
        verify(tasks).setAssignee("a", "99");
        verify(runtime).setVariableLocal("exec-a", "reviewer", "99");
        verify(runtime).deleteMultiInstanceExecution("exec-b", false);
        verify(runtime, never()).addMultiInstanceExecution(anyString(), anyString(), anyMap());
    }

    @Test
    void moreReviewersOnlyAddDifferenceAndUseActualElementVariable() {
        doReturn(List.of(task("a", "approve"))).when(query).list();
        assign(model(false), "99,100,100");
        verify(tasks).setAssignee("a", "99");
        verify(runtime).addMultiInstanceExecution("approve", "instance", Map.of("reviewer", "100"));
        verify(runtime, never()).deleteMultiInstanceExecution(anyString(), anyBoolean());
    }

    @Test
    void ambiguousBranchesAndSequentialMultiInstanceAreRejectedWithoutMutation() {
        doReturn(List.of(task("a", "approve"), task("b", "other"))).when(query).list();
        assertThrows(ServiceException.class, () -> assign(model(false), "99,100"));
        doReturn(List.of(task("a", "approve"))).when(query).list();
        assertThrows(ServiceException.class, () -> assign(model(true), "99"));
        assertThrows(ServiceException.class, () -> assign(model(false), "99,"));
        verify(tasks, never()).setAssignee(anyString(), anyString());
        verifyNoInteractions(runtime);
    }

    @Test
    void reservedVariablesAreRejectedBeforeTaskMutation() {
        Task current = task("current", "approve");
        when(current.getAssignee()).thenReturn("42");
        when(query.singleResult()).thenReturn(current);
        WfTaskBo bo = new WfTaskBo();
        bo.setTaskId("current");
        try (var user = mockStatic(TaskUtils.class)) {
            user.when(TaskUtils::getUserId).thenReturn("42");
            for (String key : ProcessConstants.RESERVED_VARIABLES) {
                bo.setVariables(Map.of(key, "bad"));
                assertThrows(ServiceException.class, () -> service.complete(bo));
            }
        }
        verify(tasks, never()).complete(anyString(), anyMap(), anyBoolean());
        verify(tasks, never()).claim(anyString(), anyString());
    }

    @Test
    void returnListRequiresTaskOwnershipAndHandlesMissingTask() {
        Task current = task("current", "approve");
        when(current.getAssignee()).thenReturn("other");
        when(query.singleResult()).thenReturn(current, (Task) null);
        try (var user = mockStatic(TaskUtils.class)) {
            user.when(TaskUtils::getUserId).thenReturn("42");
            assertThrows(ServiceException.class, () -> service.findReturnTaskList(new WfTaskBo()));
            assertThrows(ServiceException.class, () -> service.findReturnTaskList(new WfTaskBo()));
        }
    }
}
