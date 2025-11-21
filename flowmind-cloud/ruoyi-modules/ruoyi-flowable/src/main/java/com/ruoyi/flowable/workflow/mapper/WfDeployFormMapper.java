package com.ruoyi.flowable.workflow.mapper;


import com.ruoyi.flowable.core.mapper.BaseMapperPlus;
import com.ruoyi.flowable.workflow.domain.WfDeployForm;
import com.ruoyi.flowable.workflow.domain.vo.WfDeployFormVo;
import org.apache.ibatis.annotations.Mapper;

/**
 * 流程实例关联表单Mapper接口
 *
 * @author KonBAI
 * @createTime 2022/3/7 22:07
 */
@Mapper
public interface WfDeployFormMapper extends BaseMapperPlus<WfDeployFormMapper, WfDeployForm, WfDeployFormVo> {

}
