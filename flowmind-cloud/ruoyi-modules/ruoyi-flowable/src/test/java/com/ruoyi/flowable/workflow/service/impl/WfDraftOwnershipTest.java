package com.ruoyi.flowable.workflow.service.impl;

import com.ruoyi.common.core.exception.ServiceException;
import com.ruoyi.common.security.utils.SecurityUtils;
import com.ruoyi.flowable.workflow.domain.WfDraft;
import com.ruoyi.flowable.workflow.domain.bo.WfDraftBo;
import com.ruoyi.flowable.workflow.domain.vo.WfDraftVo;
import com.ruoyi.flowable.workflow.mapper.WfDraftMapper;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/** 草稿归属校验与用户级清理回归。 */
class WfDraftOwnershipTest {
    @Test
    void cannotReadAnotherUsersDraft() {
        var mapper = mock(WfDraftMapper.class);
        var draft = new WfDraftVo();
        draft.setUserId(2L);
        when(mapper.selectVoById(10L)).thenReturn(draft);
        try (var user = mockStatic(SecurityUtils.class)) {
            user.when(SecurityUtils::getUserId).thenReturn(1L);
            assertThrows(ServiceException.class, () -> new WfDraftServiceImpl(mapper).queryById(10L));
        }
    }

    @Test
    void cannotOverwriteAnotherUsersDraftWithSuppliedId() {
        var mapper = mock(WfDraftMapper.class);
        var draft = new WfDraft();
        draft.setUserId(2L);
        draft.setDefinitionId("definition");
        when(mapper.selectByDraftId(10L)).thenReturn(draft);
        var bo = new WfDraftBo();
        bo.setDraftId(10L);
        bo.setDefinitionId("definition");
        try (var user = mockStatic(SecurityUtils.class)) {
            user.when(SecurityUtils::getUserId).thenReturn(1L);
            assertThrows(ServiceException.class, () -> new WfDraftServiceImpl(mapper).saveOrUpdateDraft(bo));
            verify(mapper).selectByDraftId(10L);
            verifyNoMoreInteractions(mapper);
        }
    }

    @Test
    void personalCleanupAndRestoreAreScopedToCurrentUser() {
        var mapper = mock(WfDraftMapper.class);
        var service = new WfDraftServiceImpl(mapper);
        try (var user = mockStatic(SecurityUtils.class)) {
            user.when(SecurityUtils::getUserId).thenReturn(1L);
            service.deleteCurrentUserDraft("definition");
            service.restoreByDefinitionId("definition");
            verify(mapper).deleteUserDraft("definition", 1L);
            verify(mapper).restoreByDefinitionId("definition", 1L);
            verify(mapper, never()).deleteByDefinitionId(anyString());
        }
    }
}
