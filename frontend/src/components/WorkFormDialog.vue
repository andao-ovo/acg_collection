<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑作品' : '新增作品'"
    width="520px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="70px"
      label-position="left"
    >
      <el-form-item label="标题" prop="title">
        <el-input v-model="form.title" placeholder="作品名称" maxlength="100" />
      </el-form-item>

      <el-form-item label="类型" prop="type">
        <el-select v-model="form.type" placeholder="请选择类型" style="width: 100%">
          <el-option
            v-for="t in WORK_TYPE_OPTIONS"
            :key="t.value"
            :label="t.label"
            :value="t.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="作者">
        <el-input v-model="form.author" placeholder="作者 / 制作公司（可选）" />
      </el-form-item>

      <el-form-item label="状态" prop="status">
        <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
          <el-option
            v-for="s in STATUS_OPTIONS"
            :key="s.value"
            :label="s.label"
            :value="s.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="评分">
        <el-rate
          v-model="form.rating"
          :max="10"
          show-score
          :colors="['#f7b500', '#f7b500', '#f7b500']"
        />
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="form.comment"
          type="textarea"
          :rows="3"
          placeholder="你的短评 / 备注…"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="saving" @click="handleSubmit">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { createWork, updateWork } from '@/api'
import { WORK_TYPE_OPTIONS, STATUS_OPTIONS, typeInfo } from '@/constants'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 传入 null 表示新增，传入对象表示编辑
  work: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const formRef = ref()
const saving = ref(false)

const isEdit = computed(() => !!props.work)

const form = ref({
  title: '',
  type: '动漫',
  author: '',
  status: '连载中',
  rating: null,
  comment: '',
})

const rules = {
  title: [{ required: true, message: '请输入作品标题', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
}

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      if (props.work) {
        Object.assign(form.value, {
          title: props.work.title || '',
          type: typeInfo(props.work.type).label,
          author: props.work.author || '',
          status: props.work.status || '连载中',
          rating: props.work.rating ?? null,
          comment: props.work.comment || '',
        })
      } else {
        form.value = {
          title: '',
          type: '动漫',
          author: '',
          status: '连载中',
          rating: null,
          comment: '',
        }
      }
    }
  }
)

function handleClose() {
  emit('update:modelValue', false)
}

async function handleSubmit() {
  await formRef.value.validate()
  saving.value = true
  try {
    const payload = {
      title: form.value.title,
      type: form.value.type,
      author: form.value.author || null,
      status: form.value.status,
      rating: form.value.rating,
      comment: form.value.comment || null,
    }
    if (isEdit.value) {
      await updateWork(props.work.id, payload)
      ElMessage.success('修改成功')
    } else {
      await createWork(payload)
      ElMessage.success('新增成功')
    }
    emit('saved')
  } finally {
    saving.value = false
  }
}
</script>