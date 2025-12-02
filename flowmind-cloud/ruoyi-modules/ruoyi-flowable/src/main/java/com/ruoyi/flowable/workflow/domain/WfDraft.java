package com.ruoyi.flowable.workflow.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import com.ruoyi.flowable.workflow.domain.base.BaseEntity;
import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 流程草稿对象 wf_draft
 *
 * @author ruoyi
 * @createTime 2025/01/01 00:00
 */
@Data
@EqualsAndHashCode(callSuper = true)
@TableName("wf_draft")
public class WfDraft extends BaseEntity {
    private static final long serialVersionUID = 1L;

    /**
     * 草稿主键
     */
    @TableId(value = "draft_id", type = IdType.AUTO)
    private Long draftId;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 流程定义ID
     */
    private String definitionId;

    /**
     * 部署ID
     */
    private String deployId;

    /**
     * 流程名称
     */
    private String processName;

    /**
     * 表单数据(JSON格式)
     */
    private String formData;

    /**
     * 表单模型(JSON格式)
     */
    private String formModel;

    /**
     * 删除标志(0代表存在 2代表删除)
     * 逻辑删除问题 ：WfDraft实体类中使用了 @TableLogic 注解，这是一个逻辑删除标记。当 delFlag 为 "2" 时，MyBatis-Plus会认为这条记录已被删除， updateById 方法不会更新它。
     */
    @TableLogic(value = "0", delval = "2")
    private String delFlag;

}