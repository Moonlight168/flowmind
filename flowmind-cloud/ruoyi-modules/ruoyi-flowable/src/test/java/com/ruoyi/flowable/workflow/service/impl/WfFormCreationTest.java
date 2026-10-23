package com.ruoyi.flowable.workflow.service.impl;

import com.ruoyi.flowable.workflow.controller.WfFormController;
import com.ruoyi.flowable.workflow.domain.WfForm;
import com.ruoyi.flowable.workflow.domain.bo.WfFormBo;
import com.ruoyi.flowable.workflow.mapper.WfFormMapper;
import com.ruoyi.flowable.workflow.service.IWfDeployFormService;
import org.junit.jupiter.api.Test;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 新建接口返回真实主键，供 AI 精确绑定，禁止按名称反查。 */
class WfFormCreationTest {
    @Test
    void creationReturnsGeneratedIdAndPreservesRequestedFields() {
        var mapper = mock(WfFormMapper.class);
        when(mapper.insert(any(WfForm.class))).thenAnswer(invocation -> {
            WfForm form = invocation.getArgument(0);
            assertEquals("审批意见", form.getFormName());
            assertEquals("{\"widgetList\":[{\"type\":\"textarea\"}]}", form.getContent());
            form.setFormId(99L);
            return 1;
        });
        var controller = new WfFormController(new WfFormServiceImpl(mapper), mock(IWfDeployFormService.class));
        var bo = new WfFormBo();
        bo.setFormName("审批意见");
        bo.setContent("{\"widgetList\":[{\"type\":\"textarea\"}]}");
        var response = controller.add(bo);
        assertEquals(200, response.get("code"));
        assertEquals(99L, ((Map<?, ?>) response.get("data")).get("formId"));
        verify(mapper).insert(any(WfForm.class));
        verifyNoMoreInteractions(mapper);
    }
}
