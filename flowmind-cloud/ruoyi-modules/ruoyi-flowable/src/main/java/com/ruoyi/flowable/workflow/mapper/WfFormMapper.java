package com.ruoyi.flowable.workflow.mapper;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.toolkit.Constants;
import com.ruoyi.flowable.core.mapper.BaseMapperPlus;
import com.ruoyi.flowable.workflow.domain.WfForm;
import com.ruoyi.flowable.workflow.domain.vo.WfFormVo;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 流程表单Mapper接口
 *
 * @author KonBAI
 * @createTime 2022/3/7 22:07
 */
@Mapper
public interface WfFormMapper extends BaseMapperPlus<WfFormMapper, WfForm, WfFormVo> {

    List<WfFormVo> selectFormVoList(@Param(Constants.WRAPPER) Wrapper<WfForm> queryWrapper);
}
