package com.ruoyi.flowable.utils;

import cn.hutool.core.util.ObjectUtil;
import com.ruoyi.common.core.utils.StringUtils;
import com.ruoyi.common.security.auth.AuthUtil;
import com.ruoyi.common.security.utils.SecurityUtils;
import com.ruoyi.flowable.common.constant.TaskConstants;
import com.ruoyi.system.api.model.LoginUser;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * 工作流任务工具类
 *
 * @author konbai
 * @createTime 2022/4/24 12:42
 */
public class TaskUtils {
    private static final Logger log = LoggerFactory.getLogger(TaskUtils.class);

    public static String getUserId() {
        String token = SecurityUtils.getToken();
        if (StringUtils.isNotEmpty(token)) {
            LoginUser user = AuthUtil.getLoginUser(token);
            if (ObjectUtil.isNotNull(user)) {
                return  String.valueOf(user.getUserid());
            }
        }
        return "";
    }

    /**
     * 获取用户组信息
     *
     * @return candidateGroup
     */
    public static List<String> getCandidateGroup() {
        List<String> list = new ArrayList<>();


        String token = SecurityUtils.getToken();
        if (StringUtils.isNotEmpty(token)) {
            LoginUser user = AuthUtil.getLoginUser(token);
            if (ObjectUtil.isNotNull(user)) {
                if (ObjectUtil.isNotEmpty(user.getSysUser().getRoles())) {
                    user.getSysUser().getRoles().forEach(role -> list.add(TaskConstants.ROLE_GROUP_PREFIX + role.getRoleId() ));
                }
                if (ObjectUtil.isNotNull(user.getSysUser().getDeptId())) {
                    list.add(TaskConstants.DEPT_GROUP_PREFIX + user.getSysUser().getDeptId());
                }
            } else {
                log.warn("[TaskUtils] getCandidateGroup 返回空: 无法从Token获取用户信息，请检查Redis连接或Token有效性");
            }
        }
        if (list.isEmpty()) {
            log.warn("[TaskUtils] getCandidateGroup 返回空: 用户可能没有绑定角色或部门");
        }
        return list;
    }
}
