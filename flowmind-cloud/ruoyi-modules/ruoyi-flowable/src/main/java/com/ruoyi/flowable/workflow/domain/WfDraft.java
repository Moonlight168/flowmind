package com.ruoyi.flowable.workflow.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
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
     */
    private String delFlag;
}