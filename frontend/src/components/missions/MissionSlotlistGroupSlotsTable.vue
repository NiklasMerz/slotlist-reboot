<template>
  <div>
    <table class="table table-striped">
      <thead>
        <tr>
          <th style="width: 1%" v-if="anyMissionSlotSelected"></th>
          <th style="width: 6%">#</th>
          <th :style="missionSlotRoleStyle">{{ $t('mission.slot.role') }}</th>
          <th :style="missionSlotPlayerStyle">{{ $t('mission.slot.player') }}</th>
          <th style="width: 28%" v-if="hasAnyMissionSlotDescription" class="slot-description-header">{{ $t('mission.slot.description') }}</th>
          <th style="width: 10%" class="text-center slot-actions-header">{{ $t('misc.actions') }}</th>
        </tr>
      </thead>
      <tbody>
        <mission-slotlist-group-slots-row v-for="missionSlot in missionSlotGroup.slots" :missionSlotDetails="missionSlot" :missionSlotGroup="missionSlotGroup" :hasAnyMissionSlotDescription="hasAnyMissionSlotDescription" :key="missionSlot.uid"></mission-slotlist-group-slots-row>
      </tbody>
      <tfoot v-show="missionSlotGroup.slots.length >= 10">
        <tr>
          <th style="width: 1%" v-if="anyMissionSlotSelected"></th>
          <th style="width: 6%">#</th>
          <th :style="missionSlotRoleStyle">{{ $t('mission.slot.role') }}</th>
          <th :style="missionSlotPlayerStyle">{{ $t('mission.slot.player') }}</th>
          <th style="width: 28%" v-if="hasAnyMissionSlotDescription" class="slot-description-header">{{ $t('mission.slot.description') }}</th>
          <th style="width: 10%" class="text-center slot-actions-header">{{ $t('misc.actions') }}</th>
        </tr>
      </tfoot>
    </table>
  </div>
</template>

<script>
import * as _ from 'lodash'

import MissionSlotlistGroupSlotsRow from './MissionSlotlistGroupSlotsRow.vue'

export default {
  components: {
    MissionSlotlistGroupSlotsRow
  },
  props: [
    'missionSlotGroup'
  ],
  computed: {
    anyMissionSlotSelected() {
      return !_.isEmpty(this.$store.getters.missionSlotSelection)
    },
    hasAnyMissionSlotDescription() {
      return _.some(this.missionSlotGroup.slots, (slot) => {
        return !_.isNil(slot.description)
      });
    },
    missionSlotPlayerStyle() {
      if (this.hasAnyMissionSlotDescription) {
        return 'width: 27%'
      } else {
        return 'width: 44%'
      }
    },
    missionSlotRoleStyle() {
      if (this.hasAnyMissionSlotDescription) {
        return 'width: 27%'
      } else {
        return 'width: 40%'
      }
    }
  }
}
</script>

<style scoped>
@media (max-width: 768px) {
  thead tr, tfoot tr {
    display: flex;
    flex-wrap: wrap;
  }
  
  thead th, tfoot th {
    box-sizing: border-box;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  
  thead th:nth-child(1), tfoot th:nth-child(1) {
    order: 1;
    flex: 0 0 auto;
    width: auto;
  }
  
  thead th:nth-child(2), tfoot th:nth-child(2) {
    order: 2;
    flex: 0 0 auto;
    width: auto;
  }
  
  thead th:nth-child(3), tfoot th:nth-child(3) {
    order: 3;
    flex: 1 1 50%;
    min-width: 0;
  }
  
  thead th:nth-child(4), tfoot th:nth-child(4) {
    order: 4;
    flex: 1 1 50%;
    min-width: 0;
  }
  
  .slot-description-header {
    order: 6 !important;
    width: 100%;
  }
  
  .slot-actions-header {
    order: 5 !important;
    width: 100%;
    text-align: left !important;
  }
}
</style>
