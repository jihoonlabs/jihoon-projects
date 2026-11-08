<script setup lang="ts">
import AttendancePage from '~/features/attendance/components/AttendancePage/AttendancePage.vue';

definePageMeta({ layout: 'dashboard', middleware: 'auth' });
</script>

<template>
  <AttendancePage />
</template>
