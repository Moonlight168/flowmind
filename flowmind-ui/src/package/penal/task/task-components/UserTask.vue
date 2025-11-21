<template>
  <div style="margin-top: 16px">
    <el-row>
      <h4 class="mb-10 fw-700">审批人设置</h4>
      <el-radio-group v-model="dataType" @change="changeDataType">
        <el-radio
          v-for="item in USER_TASK_GROUP"
          :key="item.value"
          :label="item.value"
        >{{item.label}}</el-radio>
      </el-radio-group>
    </el-row>
    <el-row>
      <el-col :span="24" v-if="dataType === USER_TASK_GROUP[0].value">
        <el-tag v-for="userText in selectedUser.text" :key="userText" effect="plain" closable @close="handleClose(userText)">
          {{userText}}
        </el-tag>
        <div class="element-drawer__button">
          <el-button size="default" type="primary" :icon="Plus" @click="onSelectUsers()">添加用户</el-button>
        </div>
      </el-col>
      <el-col :span="24" v-else-if="dataType === USER_TASK_GROUP[1].value">
        <el-select v-model="roleIds" multiple size="default" placeholder="请选择角色" @change="changeSelectRoles" style="width: 100%">
          <el-option
            v-for="item in roleOptions"
            :key="item.roleId"
            :label="item.roleName"
            :value="`ROLE${item.roleId}`"
            :disabled="item.status === 1">
          </el-option>
        </el-select>
      </el-col>
      <el-col :span="24" v-else-if="dataType === USER_TASK_GROUP[2].value">
        <el-tree-select
          v-model="deptIds"
          :data="deptTreeData"
          :props="deptProps"
           value-key="id"
           placeholder="选择部门"
           check-strictly
           clearable
           @clear="clearDept"
           ref="selectTree"
           @node-click="checkedDeptChangeNode"
           />


      </el-col>
    </el-row>
    <el-row>
      <el-col :span="24" v-show="showMultiFlog">
        <el-divider />
        <h4><b>多实例审批方式</b></h4>
        <el-row>
          <el-radio-group v-model="multiLoopType" @change="changeMultiLoopType()" class="flex-column radio-group-flex">
            <el-row v-for="item in MULTI_INSTANCE_TYPE" :key="item.value">
              <el-radio :label="item.value">{{item.label}}</el-radio>
            </el-row>
          </el-radio-group>
        </el-row>
        <el-row v-if="multiLoopType !== MULTI_INSTANCE_TYPE[0].value">
          <el-tooltip content="开启后，实例需按顺序轮流审批" placement="top-start" @click.stop.prevent>
            <el-icon><InfoFilled /></el-icon>
          </el-tooltip>
          <span class="custom-label">顺序审批：</span>
          <el-switch v-model="isSequential" @change="changeMultiLoopType()" />
        </el-row>
      </el-col>
    </el-row>

    <!-- 候选用户弹窗 -->
    <el-dialog title="候选用户" v-model="userOpen" width="60%" append-to-body>
      <el-row type="flex" :gutter="20">
        <!--部门数据-->
        <el-col :span="7">
          <el-card shadow="never" style="height: 100%">
            <div class="head-container">
              <el-input
                v-model="queryParamsDeptIds"
                placeholder="请输入部门名称"
                clearable
                size="small"
                :prefix-icon="Search"
                style="margin-bottom: 20px"
              />
              <el-tree
                :data="deptOptions"
                :props="deptProps"
                :expand-on-click-node="false"
                :filter-node-method="filterNode"
                ref="deptTree"
                :default-expand-all="false"
                node-key="id"
                highlight-current
                @current-change="handleNodeClick"
              />
            </div>
          </el-card>
        </el-col>
        <el-col :span="17">
          <el-form
            :model="queryParams"
            ref="queryForm"
            size="small"
            :inline="true"
            label-width="68px"
          >
            <el-form-item label="用户名称" prop="nickName">
              <el-input
                v-model="queryParams.nickName"
                placeholder="请输入用户名称"
                clearable
                style="width: 150px"
                @keyup.enter.native="handleQuery"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :icon="Search"
                @click="handleQuery"
              >搜索</el-button>
              <el-button
                :icon="Refresh"
                @click="resetQuery"
              >重置</el-button>
            </el-form-item>
          </el-form>
          <el-table
            ref="multipleTable"
            height="600"
            v-loading="tableLoading"
            :data="userTableList"
            border
            @row-click="clickRow"
            @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="50" align="center" />
            <el-table-column label="用户名" align="center" prop="nickName" />
            <el-table-column label="部门" align="center" prop="dept.deptName" />
          </el-table>
          <pagination
            :total="userTotal"
            v-model:page="queryParams.pageNum"
            v-model:limit="queryParams.pageSize"
            @pagination="getList"
          />
        </el-col>
      </el-row>
      <template #footer class="dialog-footer">
        <el-button type="primary" size="default" @click="handleTaskUserComplete">确 定</el-button>
        <el-button size="default" @click="userOpen = false">取 消</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<script>
import { listUser, deptTreeSelect } from "@/api/system/user";
import { listRole } from "@/api/system/role";
import { Plus, Search, Refresh } from '@element-plus/icons-vue'
import { uniqBy } from 'lodash'

const USER_TASK_GROUP = [
  {
    label: "指定用户",
    value: "USERS",
  },
  {
    label: "角色",
    value: "ROLES",
  },
  {
    label: "部门",
    value: "DEPTS",
  },
  {
    label: "发起人",
    value: "INITIATOR",
  },
]
const USER_TASK_FORM = {
  dataType: '',
  assignee: '',
  candidateUsers: '',
  candidateGroups: '',
  text: '',
  deptId: '',
  // dueDate: '',
  // followUpDate: '',
  // priority: ''
}
const MULTI_INSTANCE_TYPE = [
  { label: "无", value: 'Null' },
  { label: "会签（需所有审批人同意）", value: 'SequentialMultiInstance' },
  { label: "或签（一名审批人同意即可）", value: 'ParallelMultiInstance' },
  { label: "自定义", value: 'DiyMultiInstance' },
]
export default {
  name: "UserTask",
  props: {
    id: String,
    type: String
  },
  setup() {
    
    return { Plus, Search, Refresh  }
  },
  data() {
    return {
      tableLoading: false,
      dataType: USER_TASK_GROUP[0].value,
      selectedUser: {
        ids: [],
        text: []
      },
      userOpen: false,
      deptName: undefined,
      deptOptions: [], //部门列表
      deptProps: {
        children: "children",
        label: "label",
        value: 'id'
      },
      userTableList: [],
      userTotal: 0,
      selectedUserDate: [],
      roleOptions: [],
      roleIds: [],
      deptTreeData: [],
      deptIds: [],
      queryParamsDeptIds:[],
      // 查询参数
      queryParams: {
        deptId: undefined,
        nickName: undefined,
        pageNum: 1,
        pageSize: 20,
      },
      showMultiFlog: false,
      isSequential: false,
      multiLoopType: MULTI_INSTANCE_TYPE[0].value,
    };
  },
  watch: {
    id: {
      immediate: true,
      handler() {
        this.bpmnElement = window.bpmnInstances.bpmnElement;
        this.$nextTick(() => this.resetTaskForm());
      }
    },
    // 根据名称筛选部门树
    queryParamsDeptIds(val) {
      this.$nextTick(() => {
        this.$refs.deptTree.filter(val);
     })
    }
  },
  computed: {
    USER_TASK_GROUP() { return USER_TASK_GROUP },
    MULTI_INSTANCE_TYPE() { return MULTI_INSTANCE_TYPE }
  },
  methods: {
    // 初始化变量
    async resetTaskForm() {
      const bpmnElementObj = this.bpmnElement?.businessObject;
      if (!bpmnElementObj) {
        return;
      }
      this.clearOptionsData()
      this.dataType = bpmnElementObj.dataType;
      if (this.dataType === USER_TASK_GROUP[0].value) {
        let userIdData = bpmnElementObj['candidateUsers'] || bpmnElementObj['assignee'];
        let userText = bpmnElementObj.text || [];
        if (userIdData && userIdData.toString().length > 0 && userText && userText.length > 0) {
          this.selectedUser.ids = userIdData.toString().split(',');
          this.selectedUser.text = userText.split(',');
        }
        if (this.selectedUser.ids.length > 1) {
          this.showMultiFlog = true;
        }
      } else if (this.dataType === USER_TASK_GROUP[1].value) {
        // 获取角色列表
        this.getRoleOptions();
        let roleIdData = bpmnElementObj['candidateGroups'] || [];
        if (roleIdData && roleIdData.length > 0) {
          this.roleIds = roleIdData.split(',')
        }
        this.showMultiFlog = true;
      } else if (this.dataType === USER_TASK_GROUP[2].value) {
        // 获取部门列表
        await this.getDeptTreeData();
        let deptIdData = bpmnElementObj['candidateGroups'] || [];
        if (deptIdData && deptIdData.length > 0) {
          this.deptIds = deptIdData.split(',');
          // 回显
          this.checkedDeptChange(this.deptIds);
        }
        this.showMultiFlog = true;
      }
      this.getElementLoop(bpmnElementObj);
    },
    // 清空选项数据
    clearOptionsData() {
      this.selectedUser.ids = [];
      this.selectedUser.text = [];
      this.roleIds = [];
      this.deptIds = [];
    },
    // 更新节点数据
    updateElementTask() {
      const taskObj = Object.assign({}, { ...USER_TASK_FORM })
      window.bpmnInstances.modeling.updateProperties(this.bpmnElement, taskObj);
    },
    // 查询部门下拉树结构
    getDeptOptions() {
      return new Promise((resolve, reject) => {
        if (!this.deptOptions || this.deptOptions.length <= 0) {
          // 选择部门树 数据第一次请求
          deptTreeSelect().then(response => {
            this.deptOptions = [].concat(
              [{ id: '', label: '全部', children: [] }],
              [...response.data]
            );
            this.handleNodeClick(this.deptOptions[0])
            resolve()
          })
        } else {
          // 确保选择部门树已初始化 但仍请求表格数据 复选框回显
          this.handleNodeClick(this.deptOptions[0])
        }
      });
    },
    // 查询部门下拉树结构（含部门前缀）
    getDeptTreeData() {
      function refactorTree(data) {
        return data.map(node => {
          let treeData = { id: `DEPT${node.id}`, label: node.label, parentId: node.parentId, weight: node.weight };
          if (node.children && node.children.length > 0) {
            treeData.children = refactorTree(node.children);
          }
          return treeData;
        });
      }
      return new Promise((resolve, reject) => {
        if (!this.deptTreeData || this.deptTreeData.length <= 0) {
          deptTreeSelect().then((res) => {
            this.deptTreeData = refactorTree(res.data);
            resolve()
          }).catch(() => {
            reject()
          })
        } else {
          resolve()
        }
      })
    },
    // 查询部门下拉树结构
    getRoleOptions() {
      if (!this.roleOptions || this.roleOptions.length <= 0) {
        listRole().then(response => this.roleOptions = response.rows);
      }
    },
    // 查询用户列表
    getList() {
      this.tableLoading = true
      listUser({ ...this.queryParams }).then(response => {
        this.userTableList = response.rows;
        this.userTotal = response.total;
       // this.$nextTick(() => {
         // setTimeout(() => {
         //   this.selectedUserDate.forEach(each => {
          //    const findObj = this.userTableList.find(find => find.userId === each.userId) || {}
          //    if(Object.keys(findObj).length > 0) {
         //       this.$refs.multipleTable.toggleRowSelection(findObj)
         //     }
        //    })
        //  }, 500)
       // })
      }).finally(() => {
        this.tableLoading = false
      })
    },
    /** 搜索按钮操作 */
    handleQuery() {
      this.queryParams.pageNum = 1;
      this.getList();
    },
    /** 重置按钮操作 */
    resetQuery() {
      this.$refs.queryForm.resetFields();
      this.$refs.queryForm.clearValidate();
      this.queryParams = {
        deptId: '',
        nickName: undefined,
        pageSize: 20
      };
      this.handleQuery();
    },
    // 筛选节点
    filterNode(value, data) {
      if (!value) return true;
      return data.label.indexOf(value) !== -1;
    },
    // 节点单击事件
    handleNodeClick(data) {
      this.queryParams.deptId = data.id;
      this.handleQuery();
    },
    // 关闭标签
    handleClose(tag) {
      this.selectedUserDate.splice(this.selectedUserDate.indexOf(tag), 1);
      this.handleTaskUserChange()
    },
    /**
     * 选择行
     */
    clickRow(row) {
      this.$refs.multipleTable.toggleRowSelection(row);
    },
    // 多选框选中数据
    handleSelectionChange(selection) {
      if(selection.length) {
        const concatData = [].concat(selection, this.selectedUserDate);
        this.selectedUserDate = uniqBy(concatData, 'userId');
      }
    },
    // 添加用户
    onSelectUsers() {
      this.$nextTick(()=>
       {
          setTimeout(() => {
            this.$refs.multipleTable.clearSelection(),100
          })
      })
      this.getDeptOptions()
      this.userOpen = true;
       
    },
    // 添加用户-确认按钮
    handleTaskUserComplete() {
      if (!this.selectedUserDate || this.selectedUserDate.length <= 0) {
        this.$modal.msgError('请选择用户');
        return;
      }
      USER_TASK_FORM.dataType = USER_TASK_GROUP[0].value;
      this.handleTaskUserChange()
      this.changeMultiLoopType();
      this.userOpen = false;
    },
    // 指定用户改变确定
    handleTaskUserChange() {
      this.selectedUser.text = this.selectedUserDate.map(item => item.nickName) || [];
      if (this.selectedUserDate.length === 1) {
        let data = this.selectedUserDate[0];
        USER_TASK_FORM.assignee = data.userId;
        USER_TASK_FORM.text = data.nickName;
        USER_TASK_FORM.candidateUsers = null;
        this.showMultiFlog = false;
        this.multiLoopType = MULTI_INSTANCE_TYPE[0].value;
      } else {
        USER_TASK_FORM.candidateUsers = this.selectedUserDate.map(item => item.userId).join() || null;
        USER_TASK_FORM.text = this.selectedUserDate.map(item => item.nickName).join() || null;
        USER_TASK_FORM.assignee = null;
        this.showMultiFlog = true;
      }
      this.selectedUserDate=[];
      this.updateElementTask();
    },
    // 选中角色
    changeSelectRoles(roleArray) {
      let groups = null;
      let text = null;
      if (roleArray && roleArray.length > 0) {
        USER_TASK_FORM.dataType = USER_TASK_GROUP[1].value;
        groups = roleArray.join() || null;
        let textArr = this.roleOptions.filter(k => roleArray.indexOf(`ROLE${k.roleId}`) >= 0);
        text = textArr?.map(k => k.roleName).join() || null;
      } else {
        USER_TASK_FORM.dataType = null;
        this.multiLoopType = MULTI_INSTANCE_TYPE[0].value;
      }
      USER_TASK_FORM.candidateGroups = groups;
      USER_TASK_FORM.text = text;
      this.updateElementTask();
      this.changeMultiLoopType();
    },


    checkedDeptChangeNode(node){
     this.checkedDeptChange([node.id]);
    },
    clearDept(){
     USER_TASK_FORM.candidateGroups = "";
     USER_TASK_FORM.text = "";
     USER_TASK_FORM.assignee ="";
     USER_TASK_FORM.candidateUsers ="";
     this.updateElementTask();
     this.multiLoopType = MULTI_INSTANCE_TYPE[0].value;
     this.changeMultiLoopType();
    },
    // 选中部门
    checkedDeptChange(deptArray) {
      let groups = null;
      let text = null;
      this.deptIds = deptArray[0];
      if (deptArray && deptArray.length > 0) {
        USER_TASK_FORM.dataType = USER_TASK_GROUP[2].value;
        groups = deptArray.join(',') || null;
        let treeStarkData = JSON.parse(JSON.stringify(this.deptTreeData));
        const filterData = this.filterTreeData(treeStarkData, deptArray);
        text = filterData.map(item => item.label).join(',') || null
      } else {
        USER_TASK_FORM.dataType = null;
        this.multiLoopType = MULTI_INSTANCE_TYPE[0].value;
      }
      USER_TASK_FORM.candidateGroups = groups;
      USER_TASK_FORM.text = text;
      this.updateElementTask();
      this.changeMultiLoopType();
    },
   filterTreeData  (data, deptArray)  {
      const result = [];
      const traverse = (items) => {
        for (const item of items) {
          // 检查当前节点是否在 deptArray 中
          if (deptArray.includes(item.id)) {
            result.push(item); // 如果在，添加到结果数组中
          }

          // 如果有 children，递归处理
          if (item.children) {
            traverse(item.children);
          }
        }
      };
      traverse(data); // 开始遍历
      return result; // 返回扁平化的结果数组
  },

    // 修改审批人类型
    changeDataType(val) {
      if (val === USER_TASK_GROUP[1].value || val === USER_TASK_GROUP[2].value || (val === USER_TASK_GROUP[0].value && this.selectedUser.ids.length > 1)) {
        this.showMultiFlog = true;
      } else {
        this.showMultiFlog = false;
      }
      this.multiLoopType = MULTI_INSTANCE_TYPE[0].value;
      this.changeMultiLoopType();
      // 清空 USER_TASK_FORM 所有属性值
      Object.keys(USER_TASK_FORM).forEach(key => USER_TASK_FORM[key] = null);
      USER_TASK_FORM.dataType = val;
      if (val === USER_TASK_GROUP[0].value) {
        if (this.selectedUser && this.selectedUser.ids && this.selectedUser.ids.length > 0) {
          if (this.selectedUser.ids.length === 1) {
            USER_TASK_FORM.assignee = this.selectedUser.ids[0];
          } else {
            USER_TASK_FORM.candidateUsers = this.selectedUser.ids.join()
          }
          USER_TASK_FORM.text = this.selectedUser.text?.join() || null
        }
      } else if (val === USER_TASK_GROUP[1].value) {
        this.getRoleOptions();
        if (this.roleIds && this.roleIds.length > 0) {
          USER_TASK_FORM.candidateGroups = this.roleIds.join() || null;
          let textArr = this.roleOptions.filter(k => this.roleIds.indexOf(`ROLE${k.roleId}`) >= 0);
          USER_TASK_FORM.text = textArr?.map(k => k.roleName).join() || null;
        }
      } else if (val === USER_TASK_GROUP[2].value) {
        this.getDeptTreeData();
        if (this.deptIds && this.deptIds.length > 0) {
          USER_TASK_FORM.candidateGroups = this.deptIds.join() || null;
          let textArr = []
          let treeStarkData = JSON.parse(JSON.stringify(this.deptTreeData));
          this.deptIds.forEach(id => {
            let stark = []
            stark = stark.concat(treeStarkData);
            while(stark.length) {
              let temp = stark.shift();
              if(temp.children) {
                stark = temp.children.concat(stark);
              }
              if(id === temp.id) {
                textArr.push(temp);
              }
            }
          })
          USER_TASK_FORM.text = textArr?.map(k => k.label).join() || null;
        }
      } else {
        USER_TASK_FORM.assignee = "${initiator}";
        USER_TASK_FORM.text = "流程发起人";
      }
      this.updateElementTask();
    },
    // 初始化多实例变量
    getElementLoop(businessObject) {
      if (!businessObject.loopCharacteristics) {
        this.multiLoopType = MULTI_INSTANCE_TYPE[0].value;
        return;
      }
      this.isSequential = businessObject.loopCharacteristics.isSequential;
      if (businessObject.loopCharacteristics.completionCondition) {
        if (businessObject.loopCharacteristics.completionCondition.body === "${nrOfCompletedInstances >= nrOfInstances}") {
          this.multiLoopType = MULTI_INSTANCE_TYPE[1].value; // 会签
        } else if (businessObject.loopCharacteristics.completionCondition.body === "${nrOfCompletedInstances >= 0}") {
          this.multiLoopType = MULTI_INSTANCE_TYPE[2].value; // 或签
        } else {
          this.multiLoopType = MULTI_INSTANCE_TYPE[3].value; // 自定义
        }
      }
    },
    // 更新多实例变量
    changeMultiLoopType() {
      // 取消多实例配置
      if (this.multiLoopType === MULTI_INSTANCE_TYPE[0].value) {
        window.bpmnInstances.modeling.updateProperties(this.bpmnElement, { loopCharacteristics: null, candidateUsers: null });
        return;
      }
     
      this.multiLoopInstance = window.bpmnInstances.moddle.create("bpmn:MultiInstanceLoopCharacteristics", { isSequential: this.isSequential });
      // 更新多实例配置
      window.bpmnInstances.modeling.updateProperties(this.bpmnElement, {
        loopCharacteristics: this.multiLoopInstance,
        assignee: '${assignee}'
      });
      // 设置审批人
      USER_TASK_FORM.assignee = '${assignee}';
      // 完成条件
      let completionCondition = null;
      switch (this.multiLoopType) {
        case MULTI_INSTANCE_TYPE[1].value:
          completionCondition = window.bpmnInstances.moddle.create("bpmn:FormalExpression", { body: "${nrOfCompletedInstances >= nrOfInstances}" });
          break;
        case MULTI_INSTANCE_TYPE[2].value:
          completionCondition = window.bpmnInstances.moddle.create("bpmn:FormalExpression", { body: "${nrOfCompletedInstances > 0}" });
          break;
        default:
          completionCondition = window.bpmnInstances.moddle.create("bpmn:FormalExpression", { body: "" });
          break;
      }
      // 更新模块属性信息
      window.bpmnInstances.modeling.updateModdleProperties(this.bpmnElement, this.multiLoopInstance, {
        collection: MULTI_INSTANCE_TYPE[1].value || MULTI_INSTANCE_TYPE[2].value ? '${multiInstanceHandler.getUserIds(execution)}' : "",
        elementVariable: MULTI_INSTANCE_TYPE[1].value || MULTI_INSTANCE_TYPE[2].value ? 'assignee' : "",
        completionCondition
      });
    },
  },
  beforeDestroy() {
    this.bpmnElement = null;
  },
};
</script>
<style scoped lang="scss">
.el-row .el-radio-group {
  margin-bottom: 15px;
  .el-radio {
    line-height: 28px;
  }
}
.el-tag {
  margin-bottom: 10px;
  + .el-tag {
    margin-left: 10px;
  }
}

.custom-label {
  padding-left: 5px;
  font-weight: 500;
  font-size: 14px;
  color: #606266;
}

.head-container {
  height: 480px;
  overflow-y: auto;
}
.el-row .radio-group-flex {
  margin: 15px 0 0 0;
  justify-items: flex-start;
  align-items: flex-start !important;
}
</style>

