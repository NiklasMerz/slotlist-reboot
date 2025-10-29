<template>
  <b-popover :content="missionPopoverContent" :triggers="['hover']">
    <div class="card card-inverse calendar-mission" :class="{'card-primary': !mission.isAssignedToAnySlot && !mission.isRegisteredForAnySlot, 'card-info': !mission.isAssignedToAnySlot && mission.isRegisteredForAnySlot, 'card-success': mission.isAssignedToAnySlot}" @click="redirectToMissionDetails">
      <div class="card-header calendar-mission-title">
        <div class="mission-title-text">{{ mission.title }}</div>
        <div class="mission-community-tag" v-if="mission.community && mission.community.tag">
          [{{ mission.community.tag }}]
        </div>
      </div>
    </div>
  </b-popover>
</template>

<script>
import moment from 'moment-timezone'

export default {
  props: [
    'mission'
  ],
  computed: {
    missionPopoverContent() {
      let content = `<span><strong>${this.mission.title}</strong>`
      if (this.mission.community && this.mission.community.name) {
        content += `<br>${this.$t('community')}: ${this.mission.community.name}`
      }
      content += `<br>${this.$t('mission.startTime')} ${moment(this.mission.startTime).format('LT')}<br>${this.$t('mission.endTime')} ${moment(this.mission.endTime).format('LT')}`
      if (!this.mission.isAssignedToAnySlot && this.mission.isRegisteredForAnySlot) {
        content += `<br>${this.$t('mission.list.slot.status.registered')}</span>`
      } else if (this.mission.isAssignedToAnySlot) {
        content += `<br>${this.$t('mission.list.slot.status.assigned')}</span>`
      } else {
        content += `</span>`
      }

      return content
    }
  },
  methods: {
    redirectToMissionDetails() {
      this.$router.push({ name: 'missionDetails', params: { missionSlug: this.mission.slug } })
    }
  }
}
</script>

<style>
.calendar-mission {
  margin-bottom: 5px;
}

.calendar-mission>.calendar-mission-title {
  padding: 0px 5px;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mission-title-text {
  flex: 1;
}

.mission-community-tag {
  font-size: 10px;
  opacity: 0.9;
  font-weight: normal;
}
</style>
