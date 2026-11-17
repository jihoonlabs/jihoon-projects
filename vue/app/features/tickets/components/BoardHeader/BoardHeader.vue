<script setup lang="ts">
import type { Project } from '../../types/project';
import type { AssigneeFilter } from '../../utils/filterTickets';

defineProps<{
  projects: Project[];
  selectedProjectId: string;
}>();

const searchQuery = defineModel<string>('searchQuery', { required: true });
const assigneeFilter = defineModel<AssigneeFilter>('assigneeFilter', {
  required: true,
});

defineEmits<{ select: [projectId: string] }>();
</script>

<template>
  <header :class="$style.header">
    <h1 :class="$style.title">チケット管理</h1>

    <select
      aria-label="プロジェクト"
      :class="$style.control"
      :value="selectedProjectId"
      @change="$emit('select', ($event.target as HTMLSelectElement).value)"
    >
      <option v-if="projects.length === 0" value="ALL">
        利用可能なプロジェクトがありません
      </option>
      <template v-else>
        <option value="ALL">全プロジェクト</option>
        <option
          v-for="project in projects"
          :key="project.id"
          :value="project.id"
        >
          {{ project.name }}
        </option>
      </template>
    </select>

    <p v-if="selectedProjectId === 'ALL'" :class="$style.scope">
      <strong>全プロジェクト</strong>
      <span>編集・移動はプロジェクトを選択</span>
    </p>

    <input
      v-model="searchQuery"
      type="search"
      aria-label="チケット検索"
      placeholder="チケットを検索..."
      :class="$style.control"
    />

    <select
      v-model="assigneeFilter"
      aria-label="担当者フィルター"
      :class="$style.control"
    >
      <option value="ALL">すべての担当者</option>
      <option value="ME">自分に割り当て</option>
      <option value="UNASSIGNED">未割り当て</option>
    </select>
  </header>
</template>

<style module lang="scss">
.header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.title {
  margin-right: auto;
  font-size: 1.5rem;
}

.control {
  padding: 0.45rem 0.6rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  background: #fff;
  color: #111827;
}

.scope {
  display: flex;
  gap: 0.5rem;
  color: #4b5563;
  font-size: 0.85rem;
}
</style>
