<template>
  <tr>
    <td :data-label="$t('mission.startTime')">{{ formatDateTime(accountMission.startTime) }}</td>
    <td :data-label="$t('mission.title')">{{ accountMission.title }}</td>
    <td :data-label="$t('mission.description')">{{ accountMission.description }}</td>
    <td :data-label="$t('misc.actions')" class="text-center">
      <b-btn variant="primary" size="sm" :to="{name: 'missionDetails', params: {missionSlug: accountMission.slug}}">
        <i class="fa fa-info" aria-hidden="true"></i> {{ $t('button.details') }}
      </b-btn>
    </td>
  </tr>
</template>

<script>
export default {
  props: [
    'accountMission'
  ]
}
</script>
