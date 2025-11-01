<template>
  <tr>
    <td :data-label="$t('mission.startTime')">{{ formatDateTime(communityMission.startTime) }}</td>
    <td :data-label="$t('mission.title')">{{ communityMission.title }}</td>
    <td :data-label="$t('mission.creator')">
      <router-link :to="{name: 'userDetails', params: {userUid: communityMission.creator.uid}}">{{ formatUserWithTag(communityMission.creator) }}</router-link>
    </td>
    <td :data-label="$t('misc.actions')" class="text-center">
      <b-btn variant="primary" size="sm" :to="{name: 'missionDetails', params: {missionSlug: communityMission.slug}}">
        <i class="fa fa-info" aria-hidden="true"></i> {{ $t('button.details') }}
      </b-btn>
    </td>
  </tr>
</template>

<script>
export default {
  props: [
    'communityMission'
  ]
}
</script>
