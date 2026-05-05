/**
 * FlowMind 智能审批服务 - 分类管理工具
 *
 * 本模块提供分类检查与创建的工具函数，支持 AI 助手进行分类管理。
 */

import { listAllCategory, addCategory } from '@/api/workflow/category';

/**
 * 生成分类代码
 * @param {string} name - 分类名称
 * @returns {string} 格式化的分类代码
 */
export function generateCategoryCode(name) {
  if (!name) return '';
  // 转小写，空格替换为短横线，移除非字母数字字符
  const code = name
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '');

  // 如果结果为空（纯中文输入），使用时间戳作为后备
  if (!code) {
    return 'cat-' + Date.now().toString(36);
  }
  return code;
}

/**
 * 检查或创建分类
 * @param {string} suggestedName - 建议的分类名称
 * @param {Object} [options] - 配置选项
 * @param {boolean} [options.autoCreate=false] - 是否自动创建
 * @param {boolean} [options.showConfirm=true] - 无匹配时是否弹窗确认
 * @returns {Promise<{ categoryId: number, categoryName: string, code: string } | null>} 分类对象或 null
 */
export async function checkOrCreateCategory(suggestedName, options = {}) {
  const { autoCreate = false, showConfirm = true } = options;

  try {
    // 1. 获取分类列表
    const res = await listAllCategory();
    const categories = res.data || [];

    // 2. 查找匹配分类
    const matched = categories.find(
      (cat) =>
        cat.categoryName === suggestedName ||
        cat.code === suggestedName.toLowerCase()
    );

    if (matched) {
      // 找到匹配分类，直接返回
      return matched;
    }

    // 3. 无匹配分类
    if (autoCreate) {
      // 自动创建模式
      const createRes = await addCategory({
        categoryName: suggestedName,
        code: generateCategoryCode(suggestedName),
        remark: '由 AI 助手自动创建',
      });
      return createRes.data;
    }

    if (showConfirm) {
      // 确认创建模式 - 由调用方处理弹窗
      return null;
    }

    // 既不自动创建也不确认，返回 null
    return null;
  } catch (error) {
    console.error('分类检查失败:', error);
    return null;
  }
}

/**
 * 检查分类是否存在
 * @param {string} name - 分类名称
 * @returns {Promise<{ categoryId: number, categoryName: string, code: string } | null>} 匹配的分类对象或 null
 */
export async function checkCategoryExists(name) {
  try {
    const res = await listAllCategory();
    const categories = res.data || [];

    return (
      categories.find(
        (cat) =>
          cat.categoryName === name || cat.code === name.toLowerCase()
      ) || null
    );
  } catch (error) {
    console.error('检查分类失败:', error);
    return null;
  }
}

export default {
  checkOrCreateCategory,
  generateCategoryCode,
  checkCategoryExists,
};
