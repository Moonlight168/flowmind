package com.ruoyi.flowable.workflow.mapper;


import com.ruoyi.flowable.core.mapper.BaseMapperPlus;
import com.ruoyi.flowable.workflow.domain.WfCopy;
import com.ruoyi.flowable.workflow.domain.vo.WfCopyVo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 流程抄送Mapper接口
 *
 * @author KonBAI
 * @date 2022-05-19
 */
@Mapper
public interface WfCopyMapper extends BaseMapperPlus<WfCopyMapper, WfCopy, WfCopyVo> {
    
    /**
     * 统计当前用户的抄送数量
     *
     * @param userId 用户ID
     * @return 抄送数量
     */
    Long countByUserId(@Param("userId") Long userId);
}
