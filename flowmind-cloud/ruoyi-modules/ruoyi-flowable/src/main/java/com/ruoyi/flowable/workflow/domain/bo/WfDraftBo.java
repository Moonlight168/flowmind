package com.ruoyi.flowable.workflow.domain.bo;

import com.ruoyi.common.core.web.domain.BaseEntity;
import com.ruoyi.flowable.common.validate.AddGroup;
import com.ruoyi.flowable.common.validate.EditGroup;
import lombok.Data;
import lombok.EqualsAndHashCode;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * 流程草稿业务对象
 *
 * @author ruoyi
 * @createTime 2025/01/01 00:00
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class WfDraftBo extends BaseEntity {
    private static final long serialVersionUID = 1L;

    /**
     * 草稿主键
     */
    @NotNull(message = "草稿ID不能为空", groups = { EditGroup.class })
    private Long draftId;

    /**
     * 用户ID
     */
    @NotNull(message = "用户ID不能为空", groups = { AddGroup.class, EditGroup.class})
    private Long userId;

    /**
     * 流程定义ID
     */
    @NotBlank(message = "流程定义ID不能为空", groups = { AddGroup.class, EditGroup.class })
    private String definitionId;

    /**
     * 部署ID
     */
    private String deployId;

    /**
     * 流程名称
     */
    @NotBlank(message = "流程名称不能为空", groups = {AddGroup.class, EditGroup.class})
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