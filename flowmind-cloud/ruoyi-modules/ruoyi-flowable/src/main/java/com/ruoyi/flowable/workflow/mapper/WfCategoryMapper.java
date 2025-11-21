package com.ruoyi.flowable.workflow.mapper;


import com.ruoyi.flowable.core.mapper.BaseMapperPlus;
import com.ruoyi.flowable.workflow.domain.WfCategory;
import com.ruoyi.flowable.workflow.domain.vo.WfCategoryVo;
import org.apache.ibatis.annotations.Mapper;

/**
 * 流程分类Mapper接口
 *
 * @author KonBAI
 * @date 2022-01-15
 */
@Mapper
public interface WfCategoryMapper extends BaseMapperPlus<WfCategoryMapper, WfCategory, WfCategoryVo> {

}
