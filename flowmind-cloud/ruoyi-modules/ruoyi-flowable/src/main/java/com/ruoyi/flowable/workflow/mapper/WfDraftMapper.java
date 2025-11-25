package com.ruoyi.flowable.workflow.mapper;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.toolkit.Constants;
import com.ruoyi.flowable.core.mapper.BaseMapperPlus;
import com.ruoyi.flowable.workflow.domain.WfDraft;
import com.ruoyi.flowable.workflow.domain.vo.WfDraftVo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 流程草稿Mapper接口
 *
 * @author ruoyi
 * @createTime 2025/01/01 00:00
 */
@Mapper
public interface WfDraftMapper extends BaseMapperPlus<WfDraftMapper, WfDraft, WfDraftVo> {

    List<WfDraftVo> selectDraftVoList(@Param(Constants.WRAPPER) Wrapper<WfDraft> queryWrapper);

    /**
     * 根据用户ID和流程定义ID查询草稿
     *
     * @param userId 用户ID
     * @param definitionId 流程定义ID
     * @return 草稿
     */
    WfDraftVo selectByUserIdAndDefId(@Param("userId") Long userId, @Param("definitionId") String definitionId);
}