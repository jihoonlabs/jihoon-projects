<script setup lang="ts">
import AttendancePage from '~/features/attendance/components/AttendancePage/AttendancePage.vue';
import { pageTitle } from '~/shared/utils/pageTitle';

definePageMeta({ layout: 'dashboard', middleware: 'auth' });
useHead({ title: pageTitle('勤怠管理') });
</script>

<template>
  <AttendancePage />
</template>
