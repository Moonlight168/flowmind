/**
 * FlowMind 智能审批服务 - AI 会话管理 Store
 *
 * 本模块实现 AI 会话状态管理，提供会话 ID、进度状态、分类信息的存储和恢复能力。
 * 支持 localStorage 持久化，确保页面刷新后会话不丢失。
 */

import { defineStore } from 'pinia';
import { getAiFormState } from '@/api/workflow/ai';

// localStorage key
const STORAGE_KEY = 'aiSession';

// 默认状态
const getDefaultState = () => ({
  threadId: null,
  currentPhase: 'chatting',
  targetPageType: null,
  category: {
    categoryId: null,
    categoryName: '',
    code: ''
  },
  generatedData: {
    bpmnXml: '',
    formJson: '',
    modelName: '',
    formName: ''
  }
});

const useAiSessionStore = defineStore('aiSession', {
  state: () => getDefaultState(),

  getters: {
    /**
     * 是否有活跃会话
     */
    hasActiveSession: (state) => !!state.threadId,

    /**
     * 目标页面类型是否为流程
     */
    isFlowTarget: (state) => state.targetPageType === 'flow',

    /**
     * 目标页面类型是否为表单
     */
    isFormTarget: (state) => state.targetPageType === 'form'
  },

  actions: {
    /**
     * 初始化会话
     * @param {Object} params - 会话参数
     * @param {string} params.threadId - 会话 ID
     * @param {'flow' | 'form'} params.targetPageType - 目标页面类型
     * @param {Object} params.category - 分类信息
     */
    initializeSession({ threadId, targetPageType, category }) {
      this.threadId = threadId;
      this.targetPageType = targetPageType;
      if (category) {
        this.category = {
          categoryId: category.categoryId || null,
          categoryName: category.categoryName || '',
          code: category.code || ''
        };
      }
      this.currentPhase = 'chatting';
      this.persistState();
    },

    /**
     * 更新当前阶段
     * @param {'chatting' | 'designing' | 'done'} phase - 阶段名称
     */
    updatePhase(phase) {
      this.currentPhase = phase;
      this.persistState();
    },

    /**
     * 设置分类信息
     * @param {Object} category - 分类信息
     */
    setCategory(category) {
      this.category = {
        categoryId: category.categoryId || null,
        categoryName: category.categoryName || '',
        code: category.code || ''
      };
      this.persistState();
    },

    /**
     * 更新生成数据（合并而非覆盖）
     * @param {Object} data - 生成数据
     */
    setGeneratedData(data) {
      this.generatedData = {
        ...this.generatedData,
        ...data
      };
      this.persistState();
    },

    /**
     * 设置流程数据
     * @param {Object} flowData - 流程数据
     * @param {string} flowData.bpmnXml - BPMN XML内容
     * @param {string} flowData.modelName - 模型名称
     * @param {Object} flowData.category - 分类信息
     */
    setFlowData({ bpmnXml, modelName, category }) {
      this.generatedData.bpmnXml = bpmnXml;
      this.generatedData.modelName = modelName;
      if (category) {
        this.category = {
          categoryId: category.categoryId || null,
          categoryName: category.categoryName || '',
          code: category.code || ''
        };
      }
      this.persistState();
    },

    /**
     * 设置表单数据
     * @param {Object} formData - 表单数据
     * @param {string} formData.formJson - 表单JSON内容
     * @param {string} formData.formName - 表单名称
     */
    setFormData({ formJson, formName }) {
      this.generatedData.formJson = formJson;
      this.generatedData.formName = formName;
      this.persistState();
    },

    /**
     * 重置会话
     */
    resetSession() {
      this.$state = getDefaultState();
      localStorage.removeItem(STORAGE_KEY);
    },

    /**
     * 持久化状态到 localStorage
     */
    persistState() {
      const stateToSave = {
        threadId: this.threadId,
        currentPhase: this.currentPhase,
        targetPageType: this.targetPageType,
        category: this.category,
        generatedData: this.generatedData
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
    },

    /**
     * 从 localStorage 和后端 API 恢复会话
     * @returns {Promise<Array|null>} 恢复的聊天历史消息数组，如果无会话则返回 null
     */
    async restoreSession() {
      try {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (!saved) {
          return null;
        }

        const parsed = JSON.parse(saved);
        if (!parsed.threadId) {
          return null;
        }

        // 恢复基本状态
        this.threadId = parsed.threadId;
        this.currentPhase = parsed.currentPhase || 'chatting';
        this.targetPageType = parsed.targetPageType || null;
        this.category = parsed.category || getDefaultState().category;
        this.generatedData = parsed.generatedData || getDefaultState().generatedData;

        // 从后端获取完整聊天历史（兼容 res.data 与直出对象）
        const response = await getAiFormState(parsed.threadId);
        const state = response?.data || response;
        if (state && Array.isArray(state.messages)) {
          // 转换消息格式：{ role: 'user' | 'assistant', content: string, time: string }
          return state.messages.map((msg, index) => ({
            role: typeof msg === 'object' && msg?.role ? msg.role : (index % 2 === 0 ? 'user' : 'assistant'),
            content: typeof msg === 'string' ? msg : msg?.content || '',
            time: new Date().toISOString()
          }));
        }

        return null;
      } catch (error) {
        console.error('[aiSession] restoreSession failed:', error);
        return null;
      }
    }
  }
});

export default useAiSessionStore;
export { useAiSessionStore, initializeSession, restoreSession, persistState };

/**
 * 辅助函数：初始化会话（便捷调用）
 * @param {Object} params - 会话参数
 */
function initializeSession(params) {
  const store = useAiSessionStore();
  store.initializeSession(params);
}

/**
 * 辅助函数：恢复会话（便捷调用）
 * @returns {Promise<Array|null>} 聊天历史消息数组
 */
async function restoreSession() {
  const store = useAiSessionStore();
  return store.restoreSession();
}

/**
 * 辅助函数：持久化状态（便捷调用）
 */
function persistState() {
  const store = useAiSessionStore();
  store.persistState();
}

